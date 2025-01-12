from django.test import TestCase
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.apps import apps
from datetime import datetime, timedelta


class TestDateTimeToDateMigration(TestCase):
    def test_convert_datetime_to_date(self):
        Promotion = apps.get_model("promotions", "Promotion")

        # Convert string to datetime before creating
        test_datetime = datetime.strptime(
            "2024-12-05 12:34:55.757932", "%Y-%m-%d %H:%M:%S.%f"
        )
        expected_date = test_datetime.date()

        # Create test promotion with proper datetime object
        Promotion.objects.create(
            start_date=test_datetime,
            end_date=test_datetime + timedelta(days=1),
            duration=1,
        )

        # Verify the dates
        promotion = Promotion.objects.first()
        self.assertEqual(promotion.start_date, expected_date)


from django.test import TestCase
from django.db import migrations
from django.db.migrations.executor import MigrationExecutor
from django.db import connection
from datetime import date, timedelta


class TestEndDateMigration(TestCase):
    def setUp(self):
        self.executor = MigrationExecutor(connection)

    def test_end_date_calculation(self):
        # Create test data
        Promotion = apps.get_model("promotions", "Promotion")
        start_date = date(2025, 1, 1)

        test_cases = [
            {"duration": 1, "expected_end": date(2025, 1, 1)},
            {"duration": 2, "expected_end": date(2025, 1, 2)},
            {"duration": 7, "expected_end": date(2025, 1, 7)},
        ]

        for case in test_cases:
            promotion = Promotion.objects.create(
                start_date=start_date, duration=case["duration"]
            )

            # Run migration
            self.executor.migrate([("promotions", "0008_update_promotions_end_date")])

            # Verify
            promotion.refresh_from_db()
            print(promotion.end_date)
            self.assertEqual(promotion.end_date, case["expected_end"])
