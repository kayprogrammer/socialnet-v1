# Generated by Django 4.2.3 on 2023-09-14 18:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0002_remove_chat_dm_chat_constraints_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="chat",
            name="dm_chat_constraints",
        ),
        migrations.AddConstraint(
            model_name="chat",
            constraint=models.CheckConstraint(
                check=models.Q(
                    ("ctype", "DM"),
                    ("description", None),
                    ("image", None),
                    ("name", None),
                ),
                name="dm_chat_constraints",
            ),
        ),
    ]
