from django.db import migrations
import datetime
from django.db.models.functions import TruncDate


def convert_datetime_to_date(apps, schema_editor):
    Promotion = apps.get_model("promotions", "Promotion")
    Promotion.objects.update(
        start_date=TruncDate("start_date"), end_date=TruncDate("end_date")
    )


def reverse_convert(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("promotions", "0006_alter_promotion_end_date_alter_promotion_start_date"),
    ]

    operations = [
        migrations.RunPython(convert_datetime_to_date, reverse_convert),
    ]
