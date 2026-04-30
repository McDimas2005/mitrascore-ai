import logging

from django.conf import settings
from django.db import connections
from rest_framework import serializers
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.views import APIView

from ai_services.services import ai_runtime_status
from evidence.storage import storage_runtime_status


logger = logging.getLogger(__name__)


def mask_email(value):
    if not value or "@" not in value:
        return ""
    local, domain = value.split("@", 1)
    if len(local) <= 2:
        masked_local = local[:1] + "*"
    else:
        masked_local = f"{local[:1]}***{local[-1:]}"
    return f"{masked_local}@{domain}"


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from .serializers import LoginSerializer

        serializer = LoginSerializer(data=request.data, context={"request": request})
        try:
            if not serializer.is_valid():
                errors = serializer.errors.copy()
                detail = errors.get("detail")
                if isinstance(detail, list) and len(detail) == 1:
                    errors["detail"] = str(detail[0])
                response_status = status.HTTP_401_UNAUTHORIZED if detail else status.HTTP_400_BAD_REQUEST
                return Response(errors, status=response_status)
            return Response(serializer.validated_data)
        except Exception as exc:
            logger.exception(
                "Unexpected login failure for email=%s exception=%s",
                mask_email(str(request.data.get("email", ""))),
                exc.__class__.__name__,
            )
            return Response(
                {"detail": "Unexpected login error. Please try again or contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    serializer_class = TokenRefreshSerializer


class MeView(APIView):
    def get(self, request):
        from .serializers import UserSerializer

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
