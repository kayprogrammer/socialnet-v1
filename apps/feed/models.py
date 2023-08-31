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


def slugify_two_fields(self):
    author = self.author
    return f"{author.first_name}-{author.last_name}-{self.id}"


class Post(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    text = models.TextField()
    slug = AutoSlugField(_("slug"), populate_from=slugify_two_fields, unique=True)
    image = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.author.full_name} ------ {self.text[:10]}..."

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
    slug = AutoSlugField(_("slug"), populate_from=slugify_two_fields, unique=True)

    def __str__(self):
        return f"{self.author.full_name} ------ {self.text[:10]}..."


class Reply(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name="replies"
    )
    text = models.TextField()
    slug = AutoSlugField(_("slug"), populate_from=slugify_two_fields, unique=True)

    def __str__(self):
        return f"{self.author.full_name} ------ {self.text[:10]}..."

    class Meta:
        verbose_name_plural = "Replies"


class Reaction(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rtype = models.CharField(max_length=20, choices=REACTION_CHOICES)
    post = models.ForeignKey(
        Post, related_name="reactions", on_delete=models.SET_NULL, null=True, blank=True
    )
    comment = models.ForeignKey(
        Comment,
        related_name="reactions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reply = models.ForeignKey(
        Reply,
        related_name="reactions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "post"],
                name="unique_user_post_reaction",
            ),
            models.UniqueConstraint(
                fields=["user", "comment"],
                name="unique_user_comment_reaction",
            ),
            models.UniqueConstraint(
                fields=["user", "reply"],
                name="unique_user_reply_reaction",
            ),
        ]

    def __str__(self):
        return f"{self.user.full_name} ------ {self.rtype}"
