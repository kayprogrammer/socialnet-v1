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


class Notification(BaseModel):
    """Notification model for notifications sent by system or other users."""

    sender = models.ForeignKey(
        User, related_name="notifications_from", null=True, on_delete=models.SET_NULL
    )
    receivers = models.ManyToManyField(User)

    post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True)
    comment = models.ForeignKey(Comment, on_delete=models.SET_NULL, null=True)
    reply = models.ForeignKey(Reply, on_delete=models.SET_NULL, null=True)

    text = models.TextField()
    read_by = models.ManyToManyField(User, related_name="notifications_read")

    def __str__(self):
        return str(self.id)
