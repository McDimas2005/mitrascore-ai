from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "role", "is_active", "created_at", "updated_at")


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    password = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False, write_only=True)

    default_error_messages = {
        "invalid_credentials": "Invalid email or password.",
        "inactive_account": "This account is inactive.",
        "username_not_supported": "Use email and password to log in.",
    }

    def validate(self, attrs):
        errors = {}
        if self.initial_data.get("username") and not self.initial_data.get("email"):
            errors["email"] = [self.error_messages["username_not_supported"]]
        elif not attrs.get("email"):
            errors["email"] = ["This field is required."]
        if "password" not in attrs or attrs.get("password") == "":
            errors["password"] = ["This field is required."]
        if errors:
            raise serializers.ValidationError(errors)

        email = attrs["email"].strip().lower()
        password = attrs["password"]

        user = self._authenticate_email(email, password)
        if user is None:
            raise serializers.ValidationError({"detail": self.error_messages["invalid_credentials"]}, code="authorization")
        if not user.is_active:
            raise serializers.ValidationError({"detail": self.error_messages["inactive_account"]}, code="authorization")

        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": self._user_payload(user),
        }

    def _authenticate_email(self, email, password):
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            User().set_password(password)
            return None
        return user if user.check_password(password) else None

    def _user_payload(self, user):
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }
