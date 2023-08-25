from rest_framework.test import APITestCase
from apps.common.utils import TestUtil
from apps.accounts.models import Jwt, Otp
from unittest import mock

from apps.common.error import ErrorCode


class TestAccounts(APITestCase):
    register_url = "/api/v1/auth/register/"
    verify_email_url = "/api/v4/auth/verify-email/"
    resend_verification_email_url = "/api/v4/auth/resend-verification-email/"
    send_password_reset_otp_url = "/api/v4/auth/send-password-reset-otp/"
    set_new_password_url = "/api/v4/auth/set-new-password/"
    login_url = "/api/v4/auth/login/"
    refresh_url = "/api/v4/auth/refresh/"
    logout_url = "/api/v4/auth/logout/"

    def setUp(self):
        self.new_user = TestUtil.new_user()
        verified_user = TestUtil.verified_user()
        self.verified_user = verified_user

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

    def test_verify_email(self):
        new_user = self.new_user
        otp = "111111"
        # Verify that the email verification fails with an invalid otp
        response = self.client.post(
            self.verify_email_url, {"email": new_user.email, "otp": otp}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "code": ErrorCode.INCORRECT_OTP,
                "message": "Incorrect Otp",
            },
        )

        # Verify that the email verification succeeds with a valid otp
        otp = Otp.objects.create(user_id=new_user.id, code=otp)
        mock.patch("apps.accounts.emails.Util", new="")
        response = self.client.post(
            self.verify_email_url,
            {"email": new_user.email, "otp": otp.code},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "success", "message": "Account verification successful"},
        )

    def test_resend_verification_email(self):
        new_user = self.new_user
        user_in = {"email": new_user.email}

        # Verify that an unverified user can get a new email
        mock.patch("apps.accounts.emails.Util", new="")
        # Then, attempt to resend the verification email
        response = self.client.post(self.resend_verification_email_url, user_in)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"status": "success", "message": "Verification email sent"}
        )

        # Verify that a verified user cannot get a new email
        new_user.is_email_verified = True
        new_user.save()
        mock.patch("apps.accounts.emails.Util", new="")
        response = self.client.post(
            self.resend_verification_email_url,
            {"email": new_user.email},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"status": "success", "message": "Email already verified"}
        )

        # Verify that an error is raised when attempting to resend the verification email for a user that doesn't exist
        mock.patch("apps.accounts.emails.Util", new="")
        response = self.client.post(
            self.resend_verification_email_url,
            {"email": "invalid@example.com"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "code": ErrorCode.INCORRECT_OTP,
                "message": "Incorrect Email",
            },
        )

    def test_get_password_otp(self):
        verified_user = self.verified_user
        email = verified_user.email

        password = "testverifieduser123"
        user_dict = {"email": email, "password": password}

        mock.patch("apps.accounts.emails.Util", new="")
        # Then, attempt to get password reset token
        response = self.client.post(self.send_password_reset_otp_url, user_dict)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "success", "message": "Password otp sent"},
        )

        # Verify that an error is raised when attempting to get password reset token for a user that doesn't exist
        mock.patch("apps.accounts.emails.Util", new="")
        response = self.client.post(
            self.send_password_reset_otp_url,
            {"email": "invalid@example.com"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "code": ErrorCode.INCORRECT_EMAIL,
                "message": "Incorrect Email",
            },
        )

    def test_reset_password(self):
        verified_user = self.verified_user
        password_reset_data = {
            "email": verified_user.email,
            "password": "newtestverifieduserpassword123",
        }
        otp = "111111"

        # Verify that the password reset verification fails with an incorrect email
        response = self.client.post(
            self.set_new_password_url,
            {
                "email": "invalidemail@example.com",
                "otp": otp,
                "password": "newpassword",
            },
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "code": ErrorCode.INCORRECT_EMAIL,
                "message": "Incorrect Email",
            },
        )

        # Verify that the password reset verification fails with an invalid otp
        password_reset_data["otp"] = otp
        response = self.client.post(
            self.set_new_password_url,
            password_reset_data,
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "code": ErrorCode.INCORRECT_OTP,
                "message": "Incorrect Otp",
            },
        )

        # Verify that password reset succeeds
        Otp.objects.create(user_id=verified_user.id, code=otp)
        password_reset_data["otp"] = otp
        mock.patch("apps.accounts.emails.Util", new="")
        response = self.client.post(
            self.set_new_password_url,
            password_reset_data,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "success", "message": "Password reset successful"},
        )
