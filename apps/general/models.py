from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class SiteDetail(BaseModel):
    name = models.CharField(max_length=300, default="SocialNet")
    email = models.EmailField(default="kayprogrammer1@gmail.com")
    phone = models.CharField(max_length=300, default="+2348133831036")
    address = models.CharField(max_length=300, default="234, Lagos, Nigeria")
    fb = models.CharField(
        max_length=300, verbose_name=(_("Facebook")), default="https://facebook.com"
    )
    tw = models.CharField(
        max_length=300, verbose_name=(_("Twitter")), default="https://twitter.com"
    )
    wh = models.CharField(
        max_length=300,
        verbose_name=(_("Whatsapp")),
        default="https://wa.me/2348133831036",
    )
    ig = models.CharField(
        max_length=300, verbose_name=(_("Instagram")), default="https://instagram.com"
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.pk and SiteDetail.objects.exists():
            raise ValidationError("There can be only one Site Detail instance")

        return super(SiteDetail, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Site details"
