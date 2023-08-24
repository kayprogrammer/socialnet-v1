# Generated by Django 4.2.3 on 2023-08-24 16:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("cities_light", "0011_alter_city_country_alter_city_region_and_more"),
        ("accounts", "0002_group"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="bio",
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="city",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="cities_light.city",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="country",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="cities_light.country",
            ),
        ),
    ]