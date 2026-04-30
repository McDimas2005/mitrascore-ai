from django.conf import settings
from django.db import connections
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.views import APIView

from ai_services.services import ai_runtime_status
from evidence.storage import storage_runtime_status

from .serializers import UserSerializer


class LoginSerializer(TokenObtainPairSerializer):
    username_field = "email"

    def validate(self, attrs):
        attrs["email"] = attrs.get("email", "").lower()
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer


class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    serializer_class = TokenRefreshSerializer


class MeView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            raise serializers.ValidationError("Not authenticated")
        return Response(UserSerializer(request.user).data)


class RuntimeStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({**ai_runtime_status(), **storage_runtime_status()})


class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        database_reachable = False
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SELECT 1")
                database_reachable = cursor.fetchone()[0] == 1
        except Exception:
            database_reachable = False

        runtime = {**ai_runtime_status(), **storage_runtime_status()}
        status = "ok" if database_reachable else "degraded"
        return Response(
            {
                "status": status,
                "app": "MitraScore AI API",
                "environment": settings.APP_ENV,
                "mock_ai_mode": runtime["use_mock_ai"],
                "blob_mode": runtime["storage_mode"],
                "database_reachable": database_reachable,
            }
        )
