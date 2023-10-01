from django.db import models
from django.db.models import (
    Q,
    F,
    UniqueConstraint,
    CheckConstraint,
)
from django.db.models.functions import Least, Greatest
from apps.accounts.models import User

from apps.common.models import BaseModel
from apps.feed.models import Comment, Post, Reply
from django.utils.translation import gettext_lazy as _

# Create your models here.

REQUEST_STATUS_CHOICES = (
    ("PENDING", "PENDING"),
    ("ACCEPTED", "ACCEPTED"),
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
            # UniqueConstraint to prevent duplicate combinations of requester and requestee bidirectionally
            UniqueConstraint(
                Least("requester", "requestee"),
                Greatest("requester", "requestee"),
                name="bidirectional_unique_user_combination",
                violation_error_message="Friend with similar users already exists",
            ),
            # Check constraint to prevent requester and requestee from being the same user
            CheckConstraint(
                check=~Q(requester=F("requestee")),
                name="different_users",
                violation_error_message="Requester and Requestee cannot be the same",
            ),
        ]


NOTIFICATION_STATUS_CHOICES = (
    ("REACTION", "REACTION"),
    ("COMMENT", "COMMENT"),
    ("REPLY", "REPLY"),
    ("ADMIN", "ADMIN"),
)


class Notification(BaseModel):
    """Notification model for notifications sent by system or other users."""

    sender = models.ForeignKey(
        User, related_name="notifications_from", null=True, on_delete=models.SET_NULL
    )
    receivers = models.ManyToManyField(User)  # For admin notifications only
    ntype = models.CharField(
        max_length=100,
        verbose_name=_("Type"),
        choices=NOTIFICATION_STATUS_CHOICES,
        null=True,
        blank=True,
    )
    post = models.ForeignKey(
        Post, on_delete=models.SET_NULL, null=True, blank=True
    )  # For reactions only
    comment = models.ForeignKey(
        Comment, on_delete=models.SET_NULL, null=True, blank=True
    )  # For comments and reactions
    reply = models.ForeignKey(
        Reply, on_delete=models.SET_NULL, null=True, blank=True
    )  # For replies and reactions

    text = models.TextField()  # For admin notifications only
    read_by = models.ManyToManyField(User, related_name="notifications_read")

    def __str__(self):
        return str(self.id)

    # Set constraints
