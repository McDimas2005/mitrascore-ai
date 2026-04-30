from django.contrib.auth import authenticate
from django.test import TestCase, override_settings
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import User, UserRole


@override_settings(ALLOWED_HOSTS=["testserver"], SECURE_SSL_REDIRECT=False)
class LoginApiTests(TestCase):
    password = "Demo123!"

    @classmethod
    def setUpTestData(cls):
        cls.demo_users = {
            "umkm@mitrascore.demo": ("Ibu Sari", UserRole.UMKM_OWNER),
            "umkm2@mitrascore.demo": ("Pak Andi Test UMKM", UserRole.UMKM_OWNER),
            "fieldagent@mitrascore.demo": ("Budi Field Agent", UserRole.FIELD_AGENT),
            "analyst@mitrascore.demo": ("Rina Credit Analyst", UserRole.ANALYST),
            "admin@mitrascore.demo": ("Admin MitraScore", UserRole.ADMIN),
        }
        for email, (full_name, role) in cls.demo_users.items():
            User.objects.create_user(
                email,
                cls.password,
                full_name=full_name,
                role=role,
                is_staff=role == UserRole.ADMIN,
                is_superuser=role == UserRole.ADMIN,
            )

    def setUp(self):
        self.client = APIClient()

    def post_login(self, payload):
        return self.client.post("/api/auth/login/", payload, format="json")

    def assert_login_success(self, email, expected_role):
        response = self.post_login({"email": email, "password": self.password})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIsInstance(response.data["access"], str)
        self.assertIsInstance(response.data["refresh"], str)
        self.assertGreater(len(response.data["access"]), 20)
        self.assertGreater(len(response.data["refresh"]), 20)
        self.assertEqual(
            set(response.data["user"].keys()),
            {"id", "email", "full_name", "role", "is_active", "created_at", "updated_at"},
        )
        self.assertEqual(response.data["user"]["email"], email)
        self.assertEqual(response.data["user"]["role"], expected_role)
        return response

    def test_owner_login_with_email_and_password(self):
        self.assert_login_success("umkm@mitrascore.demo", UserRole.UMKM_OWNER)

    def test_second_owner_login_with_email_and_password(self):
        self.assert_login_success("umkm2@mitrascore.demo", UserRole.UMKM_OWNER)

    def test_analyst_login_with_email_and_password(self):
        self.assert_login_success("analyst@mitrascore.demo", UserRole.ANALYST)

    def test_field_agent_login_with_email_and_password(self):
        self.assert_login_success("fieldagent@mitrascore.demo", UserRole.FIELD_AGENT)

    def test_admin_login_with_email_and_password(self):
        self.assert_login_success("admin@mitrascore.demo", UserRole.ADMIN)

    def test_invalid_password_returns_401_json_not_500(self):
        response = self.post_login({"email": "analyst@mitrascore.demo", "password": "wrong"})
        self.assertEqual(response.status_code, 401, response.content)
        self.assertEqual(response.data["detail"], "Invalid email or password.")

    def test_missing_email_returns_400_json_not_500(self):
        response = self.post_login({"password": self.password})
        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("email", response.data)

    def test_missing_password_returns_400_json_not_500(self):
        response = self.post_login({"email": "analyst@mitrascore.demo"})
        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("password", response.data)

    def test_username_payload_returns_clear_400_json(self):
        response = self.post_login({"username": "analyst@mitrascore.demo", "password": self.password})
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(response.data["email"][0], "Use email and password to log in.")

    def test_normal_bad_login_inputs_never_return_500(self):
        payloads = [
            {},
            {"email": ""},
            {"password": self.password},
            {"email": "analyst@mitrascore.demo"},
            {"email": "analyst@mitrascore.demo", "password": ""},
            {"email": "analyst@mitrascore.demo", "password": "wrong"},
            {"username": "analyst@mitrascore.demo", "password": self.password},
        ]
        for payload in payloads:
            with self.subTest(payload=payload):
                response = self.post_login(payload)
                self.assertNotEqual(response.status_code, 500, response.content)
                self.assertIn(response.status_code, {400, 401})

    def test_django_authenticate_accepts_demo_email(self):
        user = authenticate(email="analyst@mitrascore.demo", password=self.password)
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "analyst@mitrascore.demo")

    def test_login_supports_uppercase_email_input(self):
        response = self.post_login({"email": "ANALYST@MITRASCORE.DEMO", "password": self.password})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["user"]["email"], "analyst@mitrascore.demo")

    def test_login_token_fallback_still_returns_valid_access_token(self):
        with patch("accounts.serializers.RefreshToken.for_user", side_effect=RuntimeError("token backend unavailable")):
            response = self.post_login({"email": "analyst@mitrascore.demo", "password": self.password})
        self.assertEqual(response.status_code, 200, response.content)
        validated = JWTAuthentication().get_validated_token(response.data["access"])
        self.assertEqual(validated["user_id"], User.objects.get(email="analyst@mitrascore.demo").id)
