from datetime import datetime, timezone
import uuid

from django.conf import settings
import jwt
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

        access, refresh = self._token_pair(user)
        return {
            "refresh": refresh,
            "access": access,
            "user": self._user_payload(user),
        }

    def _authenticate_email(self, email, password):
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            User().set_password(password)
            return None
        return user if user.check_password(password) else None

    def _token_pair(self, user):
        try:
            refresh = RefreshToken.for_user(user)
            return str(refresh.access_token), str(refresh)
        except Exception:
            return self._manual_token_pair(user)

    def _manual_token_pair(self, user):
        now = datetime.now(timezone.utc)
        signing_key = settings.SIMPLE_JWT.get("SIGNING_KEY") or settings.SECRET_KEY
        algorithm = settings.SIMPLE_JWT.get("ALGORITHM", "HS256")
        access = jwt.encode(
            {
                "token_type": "access",
                "exp": now + settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"],
                "iat": now,
                "jti": uuid.uuid4().hex,
                "user_id": user.id,
            },
            signing_key,
            algorithm=algorithm,
        )
        refresh = jwt.encode(
            {
                "token_type": "refresh",
                "exp": now + settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
                "iat": now,
                "jti": uuid.uuid4().hex,
                "user_id": user.id,
            },
            signing_key,
            algorithm=algorithm,
        )
        return access, refresh

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
