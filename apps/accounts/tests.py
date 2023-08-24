from rest_framework.test import APITestCase
from unittest import mock

from apps.common.error import ErrorCode


class TestAccounts(APITestCase):
    register_url = "/api/v1/auth/register/"

    def test_register(self):
        email = "testregisteruser@example.com"
        password = "testregisteruserpassword"
        user_in = {
            "first_name": "Testregister",
            "last_name": "User",
            "email": email,
            "password": password,
            "terms_agreement": True,
        }

        # Verify that a new user can be registered successfully
        mock.patch("apps.accounts.emails.Util", new="")
        response = self.client.post(self.register_url, user_in)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Registration successful",
                "data": {"email": user_in["email"]},
            },
        )

        # Verify that a user with the same email cannot be registered again
        mock.patch("apps.accounts.emails.Util", new="")
        response = self.client.post(self.register_url, user_in)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "code": ErrorCode.INVALID_ENTRY,
                "message": "Invalid Entry",
                "data": {"email": "Email already registered!"},
            },
        )
