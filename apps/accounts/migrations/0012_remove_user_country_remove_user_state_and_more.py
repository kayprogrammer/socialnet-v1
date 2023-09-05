# Generated by Django 4.2.3 on 2023-09-05 01:59

import apps.accounts.models
import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0011_alter_user_username"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="country",
        ),
        migrations.RemoveField(
            model_name="user",
            name="state",
        ),
        migrations.AlterField(
            model_name="user",
            name="username",
            field=autoslug.fields.AutoSlugField(
                always_update=True,
                editable=False,
                populate_from=apps.accounts.models.slugify_two_fields,
                unique=True,
                verbose_name="Username",
            ),
        ),
    ]
