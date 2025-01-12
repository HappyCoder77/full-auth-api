from django.core.exceptions import ValidationError
import datetime
from dateutil import tz
from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.utils import timezone

from .factories import PromotionFactory
from ..models import Promotion

TODAY = timezone.now().date()


class PromotionTestCase(TestCase):
    def setUp(self):
        """Clean up any existing promotions before each test."""
        Promotion.objects.all().delete()

    def tearDown(self):
        """Clean up promotions after each test."""
        Promotion.objects.all().delete()

    def check_remaining_time(self, promotion):
        period = relativedelta(promotion.end_date, promotion.start_date)

        if promotion.duration == 1:
            return "Esta promoción termina hoy a la medianoche."

        elif period.months < 1:
            remaining_days = (promotion.end_date - promotion.start_date).days + 1
            return f"Esta promoción termina en {remaining_days} días."
        else:
            return (
                f"Esta promoción termina en {period.months} meses y {period.days} días."
            )

    def test_Promotion_today_data(self):
        # Estos registros se crean sin validación para casos de prueba
        promotion_today = PromotionFactory()
        promotion_today_two_days = PromotionFactory(duration=2, pack_cost=3)
        promotion_today2 = PromotionFactory(duration=27, pack_cost=3)
        promotion_today3 = PromotionFactory(duration=90, pack_cost=5)

        promotion_end_date = promotion_today.start_date + relativedelta(
            days=+(promotion_today.duration - 1)
        )
        promotion_today_two_days_end_date = (
            promotion_today_two_days.start_date
            + relativedelta(days=+promotion_today_two_days.duration - 1)
        )
        promotion_end_date2 = promotion_today2.start_date + relativedelta(
            days=+promotion_today2.duration - 1
        )
        promotion_end_date3 = promotion_today3.start_date + relativedelta(
            days=+promotion_today3.duration - 1
        )

        self.assertEqual(
            promotion_today.start_date.strftime("%m/%d/%Y"), TODAY.strftime("%m/%d/%Y")
        )
        self.assertEqual(promotion_today.end_date, promotion_end_date)
        self.assertEqual(
            promotion_today_two_days.end_date, promotion_today_two_days_end_date
        )
        self.assertEqual(promotion_today2.end_date, promotion_end_date2)
        self.assertEqual(promotion_today3.end_date, promotion_end_date3)
        self.assertEqual(promotion_today.duration, 1)
        self.assertEqual(promotion_today2.duration, 27)
        self.assertEqual(promotion_today3.duration, 90)
        self.assertEqual(promotion_today.pack_cost, 1.5)
        self.assertEqual(promotion_today2.pack_cost, 3)
        self.assertEqual(promotion_today3.pack_cost, 5)
        self.assertEqual(
            promotion_today.remaining_time,
            "Esta promoción termina hoy a la medianoche.",
        )
        self.assertEqual(
            promotion_today_two_days.remaining_time, "Esta promoción termina en 2 días."
        )

        self.assertEqual(
            promotion_today2.remaining_time, self.check_remaining_time(promotion_today2)
        )
        self.assertEqual(
            promotion_today3.remaining_time, self.check_remaining_time(promotion_today3)
        )

    def test_ended_promotion_remaining_time(self):
        promotion = PromotionFactory(past=True)

        self.assertEqual(promotion.remaining_time, "Esta promoción ha terminado.")

    def test_promotion_january_data(self):
        promotion_january = PromotionFactory(
            start_date=datetime.date(2022, 1, 5),
            duration=90,
        )

        self.assertEqual(
            promotion_january.start_date,
            datetime.date(2022, 1, 5),
        )

        self.assertEqual(
            promotion_january.end_date,
            datetime.date(2022, 4, 4),
        )

        self.assertEqual(promotion_january.duration, 90)
        self.assertEqual(promotion_january.__str__(), "05 Enero 2022 / 04 Abril 2022")
        self.assertEqual(promotion_january.pack_cost, 1.5)
        self.check_remaining_time(promotion_january),

    def test_promotion_february_data(self):
        promotion_february = PromotionFactory(
            start_date=datetime.date(2022, 2, 28),
            duration=90,
        )

        self.assertEqual(promotion_february.start_date, datetime.date(2022, 2, 28))
        self.assertEqual(promotion_february.end_date, datetime.date(2022, 5, 28)),

        self.assertEqual(promotion_february.duration, 90)
        self.assertEqual(promotion_february.__str__(), "28 Febrero 2022 / 28 Mayo 2022")
        self.assertEqual(promotion_february.pack_cost, 1.5)
        self.check_remaining_time(promotion_february)

    def test_promotion_march_data(self):
        promotion_march = PromotionFactory(
            start_date=datetime.date(2022, 3, 19),
            duration=90,
        )

        self.assertEqual(
            promotion_march.start_date,
            datetime.date(2022, 3, 19),
        )
        self.assertEqual(
            promotion_march.end_date,
            datetime.date(2022, 6, 16),
        )
        self.assertEqual(promotion_march.duration, 90)
        self.assertEqual(promotion_march.__str__(), "19 Marzo 2022 / 16 Junio 2022")
        self.assertEqual(promotion_march.pack_cost, 1.5)
        self.check_remaining_time(promotion_march)

    def test_promotion_july_data(self):
        promotion_july = PromotionFactory(
            start_date=datetime.date(2022, 7, 24),
            duration=90,
        )

        self.assertEqual(
            promotion_july.start_date,
            datetime.date(2022, 7, 24),
        )
        self.assertEqual(
            promotion_july.end_date,
            datetime.date(2022, 10, 21),
        )
        self.assertEqual(promotion_july.duration, 90)
        self.assertEqual(promotion_july.__str__(), "24 Julio 2022 / 21 Octubre 2022")
        self.assertEqual(promotion_july.pack_cost, 1.5)
        self.check_remaining_time(promotion_july)

    def test_promotion_august_data(self):
        promotion_august = PromotionFactory(
            start_date=datetime.date(2022, 8, 10),
            duration=90,
        )

        self.assertEqual(
            promotion_august.start_date,
            datetime.date(2022, 8, 10),
        )

        self.assertEqual(
            promotion_august.end_date,
            datetime.date(2022, 11, 7),
        )
        self.assertEqual(promotion_august.duration, 90)
        self.assertEqual(
            promotion_august.__str__(), "10 Agosto 2022 / 07 Noviembre 2022"
        )
        self.assertEqual(promotion_august.pack_cost, 1.5)
        self.check_remaining_time(promotion_august)

    def test_promotion_september_data(self):
        promotion_september = PromotionFactory(
            start_date=datetime.date(2022, 9, 9),
            duration=90,
        )

        self.assertEqual(
            promotion_september.start_date,
            datetime.date(2022, 9, 9),
        )
        self.assertEqual(
            promotion_september.end_date,
            datetime.date(2022, 12, 7),
        )
        self.assertEqual(promotion_september.duration, 90)
        self.assertEqual(
            promotion_september.__str__(), "09 Septiembre 2022 / 07 Diciembre 2022"
        )
        self.assertEqual(promotion_september.pack_cost, 1.5)
        self.check_remaining_time(promotion_september)


class PromotionValidationTestCase(TestCase):

    def setUp(self):
        """Clean up any existing promotions before each test."""
        Promotion.objects.all().delete()

    def tearDown(self):
        """Clean up promotions after each test."""
        Promotion.objects.all().delete()

    def test_promotion_negative_pack_cost(self):
        """Test to ensure ValidationError is raised for negative envelope cost."""
        promotion = PromotionFactory.build(pack_cost=-1, balances_created=True)
        with self.assertRaises(ValidationError) as context:
            promotion.full_clean()
        error_messages = context.exception.messages
        self.assertIn(
            "El costo del pack no puede ser una cantidad negativa", error_messages
        )

    def test_overlapping_promotion(self):
        """Test to ensure ValidationError is raised for overlapping promotions."""
        # Create an initial promotion
        promotion = PromotionFactory(duration=16, balances_created=True)

        # Try to create an overlapping promotion
        overlapping_promotion = PromotionFactory.build(
            start_date=timezone.now() + timezone.timedelta(days=15)
        )

        with self.assertRaises(ValidationError) as context:
            overlapping_promotion.full_clean()

        error_messages = context.exception.messages
        self.assertIn("Ya hay una promoción en curso", error_messages)
        promotion.delete()

    def test_promotion_no_overlapping(self):
        """Test to ensure promotions do not overlap by setting non-overlapping dates."""

        promotion1 = PromotionFactory(balances_created=True)
        promotion2 = PromotionFactory.build(
            start_date=promotion1.end_date + relativedelta(days=5), duration=5
        )

        try:
            promotion2.full_clean()
        except ValidationError:  # pragma: no cover
            self.fail("clean() raised ValidationError unexpectedly!")

    def test_promotion_no_previous_promotions(self):
        """Test to ensure validation works when there are no previous promotions."""
        promotion = PromotionFactory(balances_created=True)
        try:
            promotion.full_clean()
        except ValidationError:  # pragma: no cover
            self.fail("clean() raised ValidationError unexpectedly!")

    def test_unclosed_promotions(self):
        """Test to ensure ValidationError is raised when there are unclosed promotions."""
        PromotionFactory(balances_created=False)
        promotion = PromotionFactory.build(balances_created=True)
        with self.assertRaises(ValidationError) as context:
            promotion.full_clean()
        error_messages = context.exception.messages
        self.assertIn(
            "Hay promociones sin cerrar, no se puede crear una nueva promoción.",
            error_messages,
        )
