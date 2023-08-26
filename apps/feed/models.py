from autoslug import AutoSlugField
from django.db import models
from apps.accounts.models import User
from django.utils.translation import gettext_lazy as _
from apps.common.file_processors import FileProcessor

from apps.common.models import BaseModel, File

# Create your models here.

REACTION_CHOICES = (
    ("LIKE", "LIKE"),
    ("LOVE", "LOVE"),
    ("HAHA", "HAHA"),
    ("WOW", "WOW"),
    ("SAD", "SAD"),
    ("ANGRY", "ANGRY"),
)


class Reaction(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rtype = models.CharField(max_length=20, choices=REACTION_CHOICES)


def slugify_two_fields(self):
    author = self.author
    return f"{author.first_name}-{author.last_name}-{self.id}"


class Post(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    text = models.TextField()
    slug = AutoSlugField(_("slug"), populate_from=slugify_two_fields, unique=True)
    image = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True)
    reactions = models.ManyToManyField(Reaction, blank=True)

    @property
    def get_image(self):
        image = self.image
        if image:
            return FileProcessor.generate_file_url(
                key=self.image_id,
                folder="posts",
                content_type=image.resource_type,
            )
        return None

    class Meta:
        ordering = ["-created_at"]


class Comment(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    reactions = models.ManyToManyField(Reaction, blank=True)


class Reply(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name="replies"
    )
    text = models.TextField()
    reactions = models.ManyToManyField(Reaction, blank=True)
