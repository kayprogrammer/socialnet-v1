from django.db import models
from django.db.models import CheckConstraint, Q
from django.db.models.signals import m2m_changed
from apps.accounts.models import User
from apps.common.file_processors import FileProcessor
from django.core.exceptions import ValidationError

from apps.common.models import BaseModel, File

# Create your models here.

CHAT_TYPES = (("DM", "DM"), ("GROUP", "GROUP"))


class Chat(BaseModel):
    name = models.CharField(max_length=100, null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chats")
    ctype = models.CharField(default="DM", max_length=10, choices=CHAT_TYPES)
    users = models.ManyToManyField(User, blank=True)
    description = models.CharField(max_length=1000, null=True, blank=True)
    image = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return str(self.id)

    @property
    def get_image(self):
        image = self.image
        if image:
            return FileProcessor.generate_file_url(
                key=self.image_id,
                folder="chats",
                content_type=image.resource_type,
            )
        return None

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            CheckConstraint(
                check=(Q(ctype="DM", name=None, description=None, image=None))
                | Q(ctype="GROUP"),
                name="dm_chat_constraints",
                violation_error_message="Chat with type 'DM' must have 'name', 'image' and 'description' as None",
            )
        ]


def users_changed(sender, instance, **kwargs):
    users = instance.users
    if users.count() > 1 and instance.ctype == "DM":
        raise ValidationError("You can't assign more than 1 user")
    elif instance.owner in users.all():
        raise ValidationError("Owner cannot be in users")


m2m_changed.connect(users_changed, sender=Chat.users.through)


class Message(BaseModel):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")
    text = models.TextField()
    file = models.ForeignKey(File, on_delete=models.SET_NULL, null=True)

    @property
    def get_file(self):
        file = self.file
        if file:
            return FileProcessor.generate_file_url(
                key=self.file_id,
                folder="messages",
                content_type=file.resource_type,
            )
        return None
