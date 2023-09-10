from django.db import models
from apps.accounts.models import User

from apps.common.models import BaseModel

# Create your models here.

REQUEST_STATUS_CHOICES = (
    ("PENDING", "PENDING"),
    ("ACCEPTED", "ACCEPTED"),
    ("REJECTED", "REJECTED"),
)


class Friend(BaseModel):
    requester = models.ForeignKey(
        User, related_name="requester_friends", on_delete=models.CASCADE
    )
    requestee = models.ForeignKey(
        User, related_name="requestee_friends", on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=20, default="PENDING", choices=REQUEST_STATUS_CHOICES
    )

    def __str__(self):
        return (
            f"{self.requester.full_name} & {self.requestee.full_name} --- {self.status}"
        )

    class Meta:
        constraints = [
            # UniqueConstraint to prevent duplicate combinations of requester and requestee
            models.UniqueConstraint(
                name="unique_user_combination",
                fields=["requester", "requestee"],
                condition=models.Q(requester__lt=models.F("requestee")),
            ),
            # Check constraint to prevent requester and requestee from being the same user
            models.CheckConstraint(
                check=~models.Q(requester=models.F("requestee")),
                name="different_users",
            ),
        ]
