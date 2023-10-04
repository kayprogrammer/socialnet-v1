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

from apps.profiles.utils import get_notification_message
from django.utils.safestring import mark_safe

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


NOTIFICATION_TYPE_CHOICES = (
    ("REACTION", "REACTION"),
    ("COMMENT", "COMMENT"),
    ("REPLY", "REPLY"),
    ("ADMIN", "ADMIN"),
)


class Notification(BaseModel):
    """Notification model for notifications sent by system or other users."""

    sender = models.ForeignKey(
        User,
        related_name="notifications_from",
        null=True,
        on_delete=models.SET_NULL,
        blank=True,
    )
    receivers = models.ManyToManyField(User)
    ntype = models.CharField(
        max_length=100,
        verbose_name=_("Type"),
        choices=NOTIFICATION_TYPE_CHOICES,
    )
    post = models.ForeignKey(
        Post, on_delete=models.SET_NULL, null=True, blank=True
    )  # For reactions or admin reference to a post
    comment = models.ForeignKey(
        Comment, on_delete=models.SET_NULL, null=True, blank=True
    )  # For comments and reactions
    reply = models.ForeignKey(
        Reply, on_delete=models.SET_NULL, null=True, blank=True
    )  # For replies and reactions

    text = models.CharField(
        max_length=100, blank=True, null=True
    )  # For admin notifications only
    read_by = models.ManyToManyField(
        User, related_name="notifications_read", blank=True
    )

    def __str__(self):
        return str(self.id)

    @property
    def message(self):
        text = self.text
        if not text:
            text = get_notification_message(self)
        return text

    # Set constraints

    class Meta:
        _space = "&ensp;&ensp;&nbsp;&nbsp;&nbsp;&nbsp;"
        constraints = [
            CheckConstraint(
                check=(Q(post__isnull=False, comment=None, reply=None))
                | (Q(post=None, comment__isnull=False, reply=None))
                | (Q(post=None, comment=None, reply__isnull=False))
                | (Q(post=None, comment=None, reply=None, ntype="ADMIN")),
                name="selected_object_constraints",
                violation_error_message=mark_safe(
                    f"""
                        * Cannot have cannot have post, comment, reply or any two of the three simultaneously. <br/>
                        {_space}* If the three are None, then it must be of type 'ADMIN'
                    """
                ),
            ),
            CheckConstraint(
                check=(Q(sender=None, ntype="ADMIN", text__isnull=False))
                | (Q(~Q(ntype="ADMIN"), sender__isnull=False, text=None)),
                name="sender_text_type_constraints",
                violation_error_message="If No Sender, type must be ADMIN and text must not be empty and vice versa.",
            ),
            CheckConstraint(
                check=(Q(Q(ntype="ADMIN") | Q(ntype="REACTION"), post__isnull=False))
                | (Q(Q(ntype="COMMENT") | Q(ntype="REACTION"), comment__isnull=False))
                | (Q(Q(ntype="REPLY") | Q(ntype="REACTION"), reply__isnull=False))
                | (Q(post=None, comment=None, reply=None, ntype="ADMIN")),
                name="post_comment_reply_type_constraints",
                violation_error_message=mark_safe(
                    f"""
                        * If Post, type must be ADMIN or REACTION. <br/>
                        {_space}* If Comment, type must be COMMENT or REACTION. <br/>
                        {_space}* If Reply, type must be REPLY or REACTION. <br/>
                    """
                ),
            ),
        ]

        # Validations later to ensure the read_by users are part of the receivers
