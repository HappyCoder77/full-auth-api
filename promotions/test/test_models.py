from django.core.exceptions import ValidationError
import datetime
from dateutil import tz
from dateutil.relativedelta import relativedelta
from freezegun import freeze_time
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .factories import PromotionFactory, CollectionFactory
from ..models import Promotion, Collection, Coordinate, StandardPrize, SurprisePrize

NOW = timezone.now()


class PromotionTestCase(TestCase):
    def setUp(self):
        """Clean up any existing promotions before each test."""
        Promotion.objects.all().delete()

    def tearDown(self):
        """Clean up promotions after each test."""
        Promotion.objects.all().delete()

    def check_remainig_time(self, promotion):
        period = relativedelta(
            promotion.end_date, NOW)

        if period.seconds < 0:
            self.assertEqual(
                promotion.remaining_time,
                f'Esta promoción ha terminado.'
            )
        elif period.months < 1 and period.days < 1:
            self.assertEqual(
                promotion.remaining_time,
                f'Esta promoción termina en {period.hours} horas, {period.minutes} minutos y {period.seconds} segundos.'
            ),
        elif period.months < 1:
            self.assertEqual(
                promotion.remaining_time,
                f'Esta promoción termina en {period.days} días y {period.hours} horas.'
            )

        else:
            self.assertEqual(
                promotion.remaining_time,
                f'Esta promoción termina en {period.months} meses y {period.days} días.'
            )

    def test_Promotion_today_data(self):
        now = timezone.now()
        promotion_today = PromotionFactory(
            start_date=now, current_time=now)
        promotion_today2 = PromotionFactory(
            start_date=now,
            duration=29,
            current_time=now
        )

        promotion_today3 = PromotionFactory(
            start_date=now,
            duration=90,
            current_time=now
        )

        time_range = relativedelta(days=+ promotion_today.duration)
        end_date = promotion_today.start_date + time_range

        self.assertEqual(promotion_today.start_date.strftime(
            "%m/%d/%Y"), NOW.strftime(
            "%m/%d/%Y"))
        self.assertEqual(promotion_today.end_date, end_date)
        self.assertEqual(promotion_today.duration, 1)
        self.assertEqual(promotion_today2.duration, 29)
        self.assertEqual(promotion_today3.duration, 90)
        self.assertEqual(promotion_today.envelope_cost, 1.5)
        self.check_remainig_time(promotion_today)
        self.check_remainig_time(promotion_today2)
        self.check_remainig_time(promotion_today3)

    def test_promotion_january_data(self):
        promotion_january = PromotionFactory(
            start_date=datetime.datetime(
                2022, 1, 5, 0, 0, tzinfo=tz.gettz('America/Caracas')),
            duration=90
        )

        self.assertEqual(
            promotion_january.start_date,
            datetime.datetime(2022, 1, 5, 0, 0,
                              tzinfo=tz.gettz('America/Caracas'))
        )

        self.assertEqual(
            promotion_january.end_date,
            datetime.datetime(2022, 4, 5, 0, 0,
                              tzinfo=tz.gettz('America/Caracas'))
        )

        self.assertEqual(promotion_january.duration, 90)
        self.assertEqual(promotion_january.__str__(),
                         '05 Enero 2022 / 05 Abril 2022')
        self.assertEqual(promotion_january.envelope_cost, 1.5)
        self.check_remainig_time(promotion_january)

    def test_promotion_february_data(self):
        promotion_february = PromotionFactory(
            start_date=datetime.datetime(
                2022, 2, 28, 0, 0, tzinfo=tz.gettz('America/Caracas')),
            duration=90
        )

        self.assertEqual(
            promotion_february.start_date,
            datetime.datetime(2022, 2, 28, 0, 0,
                              tzinfo=tz.gettz('America/Caracas'))
        )
        self.assertEqual(
            promotion_february.end_date,
            datetime.datetime(2022, 5, 29, 0, 0,
                              tzinfo=tz.gettz('America/Caracas'))
        )
        self.assertEqual(promotion_february.duration, 90)
        self.assertEqual(promotion_february.__str__(),
                         '28 Febrero 2022 / 29 Mayo 2022')
        self.assertEqual(promotion_february.envelope_cost, 1.5)
        self.check_remainig_time(promotion_february)

    def test_promotion_march_data(self):
        promotion_march = PromotionFactory(
            start_date=datetime.datetime(
                2022, 3, 19, 0, 0, tzinfo=tz.gettz('America/Caracas')
            ),
            duration=90
        )

        self.assertEqual(promotion_march.start_date,
                         datetime.datetime(2022, 3, 19, 0, 0,
                                           tzinfo=tz.gettz('America/Caracas'))
                         )
        self.assertEqual(
            promotion_march.end_date,
            datetime.datetime(2022, 6, 17, 0, 0,
                              tzinfo=tz.gettz('America/Caracas'))
        )
        self.assertEqual(promotion_march.duration, 90)
        self.assertEqual(promotion_march.__str__(),
                         '19 Marzo 2022 / 17 Junio 2022')
        self.assertEqual(promotion_march.envelope_cost, 1.5)
        self.check_remainig_time(promotion_march)

    def test_promotion_july_data(self):
        promotion_july = PromotionFactory(
            start_date=datetime.datetime(
                2022, 7, 24, 0, 0, tzinfo=tz.gettz('America/Caracas')
            ),
            duration=90
        )

        self.assertEqual(
            promotion_july.start_date,
            datetime.datetime(2022, 7, 24, 0, 0,
                              tzinfo=tz.gettz('America/Caracas'))
        )
        self.assertEqual(
            promotion_july.end_date,
            datetime.datetime(2022, 10, 22, 0, 0,
                              tzinfo=tz.gettz('America/Caracas'))
        )
        self.assertEqual(promotion_july.duration, 90)
        self.assertEqual(promotion_july.__str__(),
                         '24 Julio 2022 / 22 Octubre 2022')
        self.assertEqual(promotion_july.envelope_cost, 1.5)
        self.check_remainig_time(promotion_july)

    def test_promotion_august_data(self):

        promotion_august = PromotionFactory(
            start_date=datetime.datetime(
                2022, 8, 10, 0, 0, tzinfo=tz.gettz('America/Caracas')
            ),
            duration=90
        )

        self.assertEqual(
            promotion_august.start_date,
            datetime.datetime(2022, 8, 10, 0, 0,
                              tzinfo=tz.gettz('America/Caracas'))
        )

        self.assertEqual(
            promotion_august.end_date,
            datetime.datetime(2022, 11, 8, 0, 0,
                              tzinfo=tz.gettz('America/Caracas'))
        )
        self.assertEqual(promotion_august.duration, 90)
        self.assertEqual(promotion_august.__str__(),
                         '10 Agosto 2022 / 08 Noviembre 2022')
        self.assertEqual(promotion_august.envelope_cost, 1.5)
        self.check_remainig_time(promotion_august)

    def test_promotion_september_data(self):
        promotion_september = PromotionFactory(
            start_date=datetime.datetime(
                2022, 9, 9, 0, 0, tzinfo=tz.gettz('America/Caracas')
            ),
            duration=90
        )

        self.assertEqual(
            promotion_september.start_date,
            datetime.datetime(2022, 9, 9, 0, 0,
                              tzinfo=tz.gettz('America/Caracas'))
        )
        self.assertEqual(
            promotion_september.end_date,
            datetime.datetime(2022, 12, 8, 0, 0,
                              tzinfo=tz.gettz('America/Caracas'))
        )
        self.assertEqual(promotion_september.duration, 90)
        self.assertEqual(promotion_september.__str__(),
                         '09 Septiembre 2022 / 08 Diciembre 2022')
        self.assertEqual(promotion_september.envelope_cost, 1.5)
        self.check_remainig_time(promotion_september)


class PromotionValidationTestCase(TestCase):

    def setUp(self):
        """Clean up any existing promotions before each test."""
        Promotion.objects.all().delete()

    def tearDown(self):
        """Clean up promotions after each test."""
        Promotion.objects.all().delete()

    def test_promotion_negative_envelope_cost(self):
        """Test to ensure ValidationError is raised for negative envelope cost."""
        promotion = PromotionFactory.build(envelope_cost=-1)
        with self.assertRaises(ValidationError) as context:
            promotion.full_clean()
        error_messages = context.exception.messages
        self.assertIn(
            'El costo del sobre no puede ser una cantidad negativa', error_messages)

    def test_overlapping_promotion(self):
        """Test to ensure ValidationError is raised for overlapping promotions."""
        # Create an initial promotion
        promotion = PromotionFactory(duration=16)

        # Try to create an overlapping promotion
        overlapping_promotion = PromotionFactory(
            start_date=timezone.now() + timezone.timedelta(days=15))

        with self.assertRaises(ValidationError) as context:
            overlapping_promotion.full_clean()

        error_messages = context.exception.messages
        self.assertIn('Ya hay una promocion en curso', error_messages)
        promotion.delete()

    def test_promotion_no_overlapping(self):
        """Test to ensure promotions do not overlap by setting non-overlapping dates."""

        promotion1 = PromotionFactory()
        promotion2 = PromotionFactory(
            start_date=promotion1.end_date + relativedelta(days=5))

        try:
            promotion2.full_clean()
        except ValidationError:
            self.fail("clean() raised ValidationError unexpectedly!")

    def test_promotion_no_previous_promotions(self):
        """Test to ensure validation works when there are no previous promotions."""
        promotion = PromotionFactory()
        try:
            promotion.full_clean()
        except ValidationError:
            self.fail("clean() raised ValidationError unexpectedly!")


class CollectionTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Set up initial data for the whole TestCase."""
        cls.cleanup()

    def setUp(self):
        """Set up clean data before each test method."""
        self.cleanup()

    def tearDown(self):
        """Clean up data after each test method."""
        self.cleanup()

    @classmethod
    def cleanup(cls):
        Collection.objects.all().delete()
        Coordinate.objects.all().delete()
        StandardPrize.objects.all().delete()
        SurprisePrize.objects.all().delete()

    def test_collection_data(self):
        collection = CollectionFactory()
        standard_coordinates = collection.coordinates.exclude(page=99).count()
        prize_coordinate = collection.coordinates.get(page=99)

        self.assertEqual(str(collection), 'Minecraft')
        self.assertEqual(collection.coordinates.count(), 25)
        self.assertEqual(collection.standard_prizes.count(), collection.PAGES)
        self.assertEqual(collection.surprise_prizes.count(),
                         collection.SURPRISE_PRIZE_OPTIONS)
        self.assertEqual(standard_coordinates, 24)
        self.assertEqual(prize_coordinate.slot, 99)
        self.assertEqual(prize_coordinate.ordinal, 0)
        self.assertEqual(float(prize_coordinate.rarity_factor),
                         collection.PRIZE_STICKER_RARITY)
        # self.assertEqual(collection.get_absolute_url(), reverse(
        #     'collection_detail', kwargs={'pk': collection.pk}))
        counter = 1
        current_page = 1

        while current_page <= collection.PAGES:
            coordinates = iter(collection.coordinates.filter(
                page=current_page).order_by('slot'))
            current_slot = 1

            while True:
                coordinate = next(coordinates, 'fin_de_archivo')

                if coordinate != 'fin_de_archivo':
                    self.assertEqual(coordinate.page, current_page)
                    self.assertEqual(coordinate.slot, current_slot)
                    self.assertEqual(coordinate.number, counter)
                    self.assertEqual(str(coordinate), str(counter))
                    current_slot += 1
                    counter += 1
                else:
                    break

            current_page += 1

        for counter in range(1, collection.PAGES + 1):
            standard_prize = collection.standard_prizes.get(page=counter)
            self.assertEqual(standard_prize.collection, collection)
            self.assertEqual(standard_prize.description,
                             'descripción de premio standard')
            self.assertEqual(standard_prize.__str__(),
                             'descripción de premio standard')

        for counter in range(1, collection.SURPRISE_PRIZE_OPTIONS + 1):
            surprise_prize = collection.surprise_prizes.get(number=counter)
            self.assertEqual(surprise_prize.description,
                             'descripción de premio sorpresa')
            self.assertEqual(str(surprise_prize),
                             'descripción de premio sorpresa')
