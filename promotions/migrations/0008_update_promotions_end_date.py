from django.db import migrations
from datetime import timedelta


def update_end_dates(apps, schema_editor):
    Promotion = apps.get_model("promotions", "Promotion")
    for promotion in Promotion.objects.all():
        promotion.end_date = promotion.start_date + timedelta(
            days=promotion.duration - 1
        )
        promotion.save()


def reverse_end_dates(apps, schema_editor):
    Promotion = apps.get_model("promotions", "Promotion")
    for promotion in Promotion.objects.all():
        promotion.end_date = promotion.start_date + timedelta(days=promotion.duration)
        promotion.save()


class Migration(migrations.Migration):
    dependencies = [
        ("promotions", "0007_convert_datetime_to_date"),
    ]

    operations = [
        migrations.RunPython(update_end_dates, reverse_end_dates),
    ]
