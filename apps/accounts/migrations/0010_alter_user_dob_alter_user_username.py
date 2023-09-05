# Generated by Django 4.2.3 on 2023-09-04 23:16

import autoslug.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0009_user_state"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="dob",
            field=models.DateField(blank=True, null=True, verbose_name="Date of Birth"),
        ),
        migrations.AlterField(
            model_name="user",
            name="username",
            field=autoslug.fields.AutoSlugField(
                always_update=True,
                editable=False,
                populate_from=["first_name", "last_name"],
                unique=True,
                verbose_name="Username",
            ),
        ),
    ]