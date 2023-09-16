# Generated by Django 4.2.3 on 2023-09-16 22:05

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0014_alter_chat_users"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="chat",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(("ctype", "GROUP"), ("name__isnull", False)),
                    ("ctype", "DM"),
                    _connector="OR",
                ),
                name="group_chat_constraints",
                violation_error_message="Chat with type 'GROUP' must not have 'name' as None",
            ),
        ),
    ]
