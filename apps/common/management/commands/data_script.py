from django.conf import settings
from apps.accounts.models import User
from apps.general.models import SiteDetail
from django.contrib.auth.hashers import make_password

class CreateData(object):
    def __init__(self) -> None:
        pass

    async def initialize(self) -> None:
        await self.create_superuser()
        await self.create_clientuser()
        await self.create_sitedetail()

    async def create_superuser(self) -> User:
        user_dict = {
            "first_name": "Test",
            "last_name": "Admin",
            "password": make_password(settings.FIRST_SUPERUSER_PASSWORD),
            "is_superuser": True,
            "is_staff": True,
            "is_email_verified": True,
        }
        superuser, created = await User.objects.aget_or_create(
            email=settings.FIRST_SUPERUSER_EMAIL, defaults=user_dict
        )
        return superuser

    async def create_clientuser(self) -> User:
        user_dict = {
            "first_name": "Test",
            "last_name": "Client",
            "password": make_password(settings.FIRST_CLIENT_PASSWORD),
            "is_email_verified": True,
        }
        client, created = await User.objects.aget_or_create(
            email=settings.FIRST_CLIENT_EMAIL, defaults=user_dict
        )
        return client

    async def create_sitedetail(self) -> SiteDetail:
        sitedetail, created = await SiteDetail.objects.aget_or_create()
        return sitedetail
