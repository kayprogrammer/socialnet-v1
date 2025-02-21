# Generated by Django 4.2.3 on 2023-09-20 12:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0001_initial"),
        ("chat", "0017_remove_chat_group_chat_constraints_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="message",
            options={"get_latest_by": "created_at"},
        ),
        migrations.AlterField(
            model_name="message",
            name="file",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="common.file",
            ),
        ),
        migrations.AlterField(
            model_name="message",
            name="text",
            field=models.TextField(null=True),
        ),
    ]
