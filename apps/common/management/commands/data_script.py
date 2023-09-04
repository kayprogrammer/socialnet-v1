from django.conf import settings
from apps.accounts.models import User
from apps.general.models import SiteDetail


class CreateData(object):
    def __init__(self) -> None:
        pass

    async def initialize(self) -> None:
        await self.create_superuser()
        await self.create_sitedetail()

    async def create_superuser(self) -> User:
        superuser = await User.objects.aget_or_none(
            email=settings.FIRST_SUPERUSER_EMAIL
        )
        user_dict = {
            "first_name": "Test",
            "last_name": "Admin",
            "email": settings.FIRST_SUPERUSER_EMAIL,
            "password": settings.FIRST_SUPERUSER_PASSWORD,
            "is_superuser": True,
            "is_staff": True,
            "is_email_verified": True,
        }
        if not superuser:
            superuser = await User.objects.acreate_user(**user_dict)
        return superuser

    async def create_sitedetail(self) -> SiteDetail:
        sitedetail, created = await SiteDetail.objects.aget_or_create()
        return sitedetail
