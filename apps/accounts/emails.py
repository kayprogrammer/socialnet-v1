from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from asgiref.sync import sync_to_async
from . import models as accounts_models
import random, threading, asyncio


class EmailThread(threading.Thread):
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()


async def mail_send(subject, body, to):
    # I usually use threading but I'm using this instead because of vercel
    print("Working...")
    email_message = EmailMessage(subject=subject, body=body, to=to)
    email_message.content_subtype = "html"
    async_email_send = sync_to_async(email_message.send)
    loop = asyncio.get_event_loop()
    loop.create_task(async_email_send())
    print("Worked")


class Util:
    async def send_activation_otp(user):
        subject = "Verify your email"
        code = random.randint(100000, 999999)
        message = render_to_string(
            "email-activation.html",
            {
                "name": user.full_name,
                "otp": code,
            },
        )
        otp = await accounts_models.Otp.objects.aget_or_none(user=user)
        if not otp:
            await accounts_models.Otp.objects.acreate(user=user, code=code)
        else:
            otp.code = code
            await otp.asave()
        await mail_send(subject, message, [user.email])
        # EmailThread(email_message).start()

    async def send_password_change_otp(user):
        subject = "Your account password reset email"
        code = random.randint(100000, 999999)
        message = render_to_string(
            "password-reset.html",
            {
                "name": user.full_name,
                "otp": code,
            },
        )
        otp = await accounts_models.Otp.objects.aget_or_none(user=user)
        if not otp:
            await accounts_models.Otp.objects.acreate(user=user, code=code)
        else:
            otp.code = code
            await otp.asave()

        email_message = EmailMessage(subject=subject, body=message, to=[user.email])
        email_message.content_subtype = "html"

        EmailThread(email_message).start()

    def password_reset_confirmation(user):
        subject = "Password Reset Successful!"
        message = render_to_string(
            "password-reset-success.html",
            {
                "name": user.full_name,
            },
        )
        email_message = EmailMessage(subject=subject, body=message, to=[user.email])
        email_message.content_subtype = "html"
        EmailThread(email_message).start()

    @staticmethod
    def welcome_email(user):
        subject = "Account verified!"
        message = render_to_string(
            "welcome.html",
            {
                "name": user.full_name,
            },
        )
        email_message = EmailMessage(subject=subject, body=message, to=[user.email])
        email_message.content_subtype = "html"
        EmailThread(email_message).start()
