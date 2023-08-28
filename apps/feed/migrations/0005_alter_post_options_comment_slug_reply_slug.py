# Generated by Django 4.2.3 on 2023-08-28 13:58

import apps.feed.models
import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("feed", "0004_alter_comment_reactions_alter_post_reactions_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="post",
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddField(
            model_name="comment",
            name="slug",
            field=autoslug.fields.AutoSlugField(
                default="wha",
                editable=False,
                populate_from=apps.feed.models.slugify_two_fields,
                unique=True,
                verbose_name="slug",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="reply",
            name="slug",
            field=autoslug.fields.AutoSlugField(
                default="wha",
                editable=False,
                populate_from=apps.feed.models.slugify_two_fields,
                unique=True,
                verbose_name="slug",
            ),
            preserve_default=False,
        ),
    ]
