import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.contrib.auth.models import User
from django.db import close_old_connections
from django.test import (
    Client,
    TestCase,
    TransactionTestCase,
    override_settings,
    skipUnlessDBFeature,
)

from .models import InviteCode


VALID_PASSWORD = "R0bust!Passphrase-2026"


class AccountEndpointTests(TestCase):
    def setUp(self):
        self.invite = InviteCode.objects.create(code="invite-test-code")

    def post_json(self, path, data, **extra):
        return self.client.post(
            path,
            data=json.dumps(data),
            content_type="application/json",
            **extra,
        )

    def register(self, username="alice", password=VALID_PASSWORD, invite_code=None):
        return self.post_json(
            "/api/accounts/register/",
            {
                "username": username,
                "password": password,
                "invite_code": invite_code or self.invite.code,
            },
        )

    def csrf_token(self):
        response = self.client.get("/api/accounts/csrf/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)
        return response.json()["csrfToken"]

    @override_settings(DEBUG=True)
    def test_development_registration_page_is_available_in_debug_mode(self):
        response = self.client.get("/api/accounts/dev/register/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/dev_registration.html")
        self.assertContains(response, 'name="invite_code"')
        self.assertContains(response, "/api/accounts/register/")

    @override_settings(DEBUG=False)
    def test_development_registration_page_is_hidden_outside_debug_mode(self):
        response = self.client.get("/api/accounts/dev/register/")

        self.assertEqual(response.status_code, 404)

    def test_successful_registration_hashes_password_and_returns_public_user(self):
        response = self.register()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(set(response.json()["user"]), {"id", "username"})
        user = User.objects.get(username="alice")
        self.assertTrue(user.check_password(VALID_PASSWORD))
        self.invite.refresh_from_db()
        self.assertTrue(self.invite.is_used)

    def test_invalid_invitation_is_rejected(self):
        response = self.register(invite_code="not-a-valid-code")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"invite_code": ["Invalid or already used invite code."]},
        )
        self.assertFalse(User.objects.exists())

    def test_registration_reports_missing_expected_invite_code_field(self):
        response = self.post_json(
            "/api/accounts/register/",
            {
                "username": "alice",
                "password": VALID_PASSWORD,
                "invitation_code": self.invite.code,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"invite_code": ["This field is required."]})
        self.assertFalse(User.objects.exists())
        self.invite.refresh_from_db()
        self.assertFalse(self.invite.is_used)

    def test_invitation_cannot_be_reused(self):
        self.assertEqual(self.register("alice").status_code, 201)

        response = self.register("bob")

        self.assertEqual(response.status_code, 400)
        self.assertIn("invite_code", response.json())
        self.assertFalse(User.objects.filter(username="bob").exists())

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(username="alice", password=VALID_PASSWORD)

        response = self.register()

        self.assertEqual(response.status_code, 400)
        self.assertIn("username", response.json())

    def test_django_password_validation_is_applied(self):
        response = self.register(password="password")

        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.json())
        self.assertFalse(User.objects.exists())
        self.invite.refresh_from_db()
        self.assertFalse(self.invite.is_used)

    def test_login_and_failed_login(self):
        User.objects.create_user(username="alice", password=VALID_PASSWORD)

        success = self.post_json(
            "/api/accounts/login/",
            {"username": "alice", "password": VALID_PASSWORD},
        )
        failure = self.post_json(
            "/api/accounts/login/",
            {"username": "alice", "password": "incorrect-password"},
        )

        self.assertEqual(success.status_code, 200)
        self.assertEqual(success.json()["user"]["username"], "alice")
        self.assertNotIn("password", success.json()["user"])
        self.assertEqual(failure.status_code, 401)
        self.assertEqual(failure.json(), {"detail": "Invalid username or password."})

    def test_logout_ends_session(self):
        user = User.objects.create_user(username="alice", password=VALID_PASSWORD)
        self.client.force_login(user)

        response = self.client.post("/api/accounts/logout/")
        current_user = self.client.get("/api/accounts/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(current_user.status_code, 401)

    def test_anonymous_user_cannot_read_current_user(self):
        response = self.client.get("/api/accounts/me/")

        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_can_read_current_user(self):
        user = User.objects.create_user(username="alice", password=VALID_PASSWORD)
        self.client.force_login(user)

        response = self.client.get("/api/accounts/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"user": {"id": user.pk, "username": "alice"}})

    def test_login_requires_csrf_token(self):
        User.objects.create_user(username="alice", password=VALID_PASSWORD)
        csrf_client = Client(enforce_csrf_checks=True)

        missing_token = csrf_client.post(
            "/api/accounts/login/",
            data=json.dumps({"username": "alice", "password": VALID_PASSWORD}),
            content_type="application/json",
        )
        token_response = csrf_client.get("/api/accounts/csrf/")
        token = token_response.json()["csrfToken"]
        valid_token = csrf_client.post(
            "/api/accounts/login/",
            data=json.dumps({"username": "alice", "password": VALID_PASSWORD}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(missing_token.status_code, 403)
        self.assertEqual(valid_token.status_code, 200)

    def test_registration_requires_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        payload = {
            "username": "alice",
            "password": VALID_PASSWORD,
            "invite_code": self.invite.code,
        }

        response_without_token = csrf_client.post(
            "/api/accounts/register/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        token = csrf_client.get("/api/accounts/csrf/").json()["csrfToken"]
        response_with_token = csrf_client.post(
            "/api/accounts/register/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response_without_token.status_code, 403)
        self.assertEqual(response_with_token.status_code, 201)

    def test_logout_requires_csrf_token(self):
        user = User.objects.create_user(username="alice", password=VALID_PASSWORD)
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(user)

        response_without_token = csrf_client.post("/api/accounts/logout/")
        token = csrf_client.get("/api/accounts/csrf/").json()["csrfToken"]
        response_with_token = csrf_client.post(
            "/api/accounts/logout/",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response_without_token.status_code, 403)
        self.assertEqual(response_with_token.status_code, 200)


@skipUnlessDBFeature("has_select_for_update")
class ConcurrentInviteConsumptionTests(TransactionTestCase):
    reset_sequences = True

    def test_only_one_concurrent_registration_consumes_an_invitation(self):
        invite = InviteCode.objects.create(code="concurrent-invite")
        barrier = Barrier(2)

        def attempt_registration(username):
            close_old_connections()
            try:
                client = Client()
                barrier.wait(timeout=10)
                response = client.post(
                    "/api/accounts/register/",
                    data=json.dumps(
                        {
                            "username": username,
                            "password": VALID_PASSWORD,
                            "invite_code": invite.code,
                        }
                    ),
                    content_type="application/json",
                )
                return response.status_code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            statuses = list(
                executor.map(attempt_registration, ("alice", "bob"))
            )

        self.assertCountEqual(statuses, (201, 400))
        self.assertEqual(User.objects.count(), 1)
        invite.refresh_from_db()
        self.assertTrue(invite.is_used)
