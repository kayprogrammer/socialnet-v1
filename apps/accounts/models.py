import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from apps.common.models import BaseModel, File
from django.conf import settings
from apps.common.file_processors import FileProcessor
from .managers import CustomUserManager


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, primary_key=True
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(verbose_name=(_("Email address")), unique=True)
    avatar = models.ForeignKey(File, on_delete=models.SET_NULL, null=True)

    terms_agreement = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def get_avatar(self):
        avatar = self.avatar
        if avatar:
            return FileProcessor.generate_file_url(
                key=self.avatar_id,
                folder="avatars",
                content_type=avatar.resource_type,
            )
        return None


class Jwt(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access = models.TextField()
    refresh = models.TextField()


class Otp(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.IntegerField()

    def check_expiration(self):
        now = timezone.now()
        diff = now - self.updated_at
        if diff.total_seconds() > int(settings.EMAIL_OTP_EXPIRE_SECONDS):
            return True
        return False
