from django.core.exceptions import ValidationError
import datetime
from dateutil import tz
from dateutil.relativedelta import relativedelta
from freezegun import freeze_time
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from unittest import skip
from .factories import (AlbumFactory, PromotionFactory, CollectionFactory,
                        EditionFactory, UserFactory)
from ..models import (Promotion, Collection, Box,
                      Pack, Sticker, Coordinate, Album)

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
        self.assertEqual(promotion_today.pack_cost, 1.5)
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
        self.assertEqual(promotion_january.pack_cost, 1.5)
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
        self.assertEqual(promotion_february.pack_cost, 1.5)
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
        self.assertEqual(promotion_march.pack_cost, 1.5)
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
        self.assertEqual(promotion_july.pack_cost, 1.5)
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
        self.assertEqual(promotion_august.pack_cost, 1.5)
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
        self.assertEqual(promotion_september.pack_cost, 1.5)
        self.check_remainig_time(promotion_september)


class PromotionValidationTestCase(TestCase):

    def setUp(self):
        """Clean up any existing promotions before each test."""
        Promotion.objects.all().delete()

    def tearDown(self):
        """Clean up promotions after each test."""
        Promotion.objects.all().delete()

    def test_promotion_negative_pack_cost(self):
        """Test to ensure ValidationError is raised for negative envelope cost."""
        promotion = PromotionFactory.build(pack_cost=-1)
        with self.assertRaises(ValidationError) as context:
            promotion.full_clean()
        error_messages = context.exception.messages
        self.assertIn(
            'El costo del pack no puede ser una cantidad negativa', error_messages)

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
        self.assertIn('Ya hay una promoción en curso', error_messages)
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
    COLLECTION_NAME = "Minecraft"

    def setUp(self):
        self.collection = CollectionFactory()

    def tearDown(self):
        """Clean up data after each test method."""
        Collection.objects.all().delete()

    def test_collection_data(self):
        standard_coordinates = self.collection.coordinates.exclude(
            page=99).count()

        self.assertEqual(standard_coordinates, 24)
        self.assertEqual(self.collection.name, self.COLLECTION_NAME)
        self.assertEqual(str(self.collection), 'Minecraft')
        self.assertEqual(self.collection.coordinates.count(), 25)
        self.assertEqual(
            self.collection.coordinates.filter(rarity_factor=self.collection.RARITY_1).count(), 8)
        self.assertEqual(
            self.collection.coordinates.filter(rarity_factor=self.collection.RARITY_2).count(), 8)
        self.assertEqual(
            self.collection.coordinates.filter(rarity_factor=self.collection.RARITY_3).count(), 4)
        self.assertEqual(
            self.collection.coordinates.filter(rarity_factor=self.collection.RARITY_4).count(), 1)
        self.assertEqual(
            self.collection.coordinates.filter(rarity_factor=self.collection.RARITY_5).count(), 1)
        self.assertEqual(
            self.collection.coordinates.filter(rarity_factor=self.collection.RARITY_6).count(), 1)
        self.assertEqual(
            self.collection.coordinates.filter(rarity_factor=self.collection.RARITY_7).count(), 1)
        self.assertEqual(
            self.collection.coordinates.filter(rarity_factor=self.collection.PRIZE_STICKER_RARITY).count(), 1)
        self.assertEqual(
            self.collection.standard_prizes.count(), self.collection.PAGES)
        self.assertEqual(self.collection.surprise_prizes.count(),
                         self.collection.SURPRISE_PRIZE_OPTIONS)

    def test_prize_coordinate_data(self):
        prize_coordinate = self.collection.coordinates.get(page=99)

        self.assertEqual(prize_coordinate.slot,
                         self.collection.PRIZE_STICKER_COORDINATE)
        self.assertEqual(prize_coordinate.rarity_factor,
                         self.collection.PRIZE_STICKER_RARITY)
        self.assertEqual(prize_coordinate.ordinal, 0)

    def test_coordinates_data(self):

        counter = 1
        current_page = 1

        while current_page <= self.collection.PAGES:
            coordinates = iter(self.collection.coordinates.filter(
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

    def test_standard_prizes_data(self):
        for counter in range(1, self.collection.PAGES + 1):
            standard_prize = self.collection.standard_prizes.get(page=counter)
            self.assertEqual(standard_prize.collection, self.collection)
            self.assertEqual(standard_prize.description,
                             'descripción de premio standard')
            self.assertEqual(standard_prize.__str__(),
                             'descripción de premio standard')

    def test_surprise_prizes_data(self):
        for counter in range(1, self.collection.SURPRISE_PRIZE_OPTIONS + 1):
            surprise_prize = self.collection.surprise_prizes.get(
                number=counter)
            self.assertEqual(surprise_prize.description,
                             'descripción de premio sorpresa')
            self.assertEqual(str(surprise_prize),
                             'descripción de premio sorpresa')


@skip("saltar")
class EditionTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.edition = EditionFactory(circulation=250)

    def test_edition_data(self):
        boxes = Box.objects.filter(edition=self.edition).order_by('pk')
        packs = Pack.objects.filter(box__edition_id=self.edition.id)

        self.assertEqual(str(self.edition), 'Minecraft')
        self.assertEqual(boxes.count(), 37)
        # self.assertEqual(packs.count(), 3695)

    def test_rarity_distribution(self):
        stickers = Sticker.objects.all()

        rarity_1_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.RARITY_1).count()

        rarity_2_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.RARITY_2).count()

        rarity_3_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.RARITY_3).count()

        rarity_4_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.RARITY_4).count()

        rarity_5_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.RARITY_5).count()

        rarity_6_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.RARITY_6).count()

        rarity_7_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.RARITY_7).count()

        surprize_prize_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.PRIZE_STICKER_RARITY).count()

        total_stickers = rarity_1_total + rarity_2_total + rarity_3_total + \
            rarity_4_total + rarity_5_total+rarity_6_total + \
            rarity_7_total+surprize_prize_total

        self.assertEqual(rarity_1_total, 6000)
        self.assertEqual(rarity_2_total, 4000)
        self.assertEqual(rarity_3_total, 1000)
        self.assertEqual(rarity_4_total, 5)
        self.assertEqual(rarity_5_total, 2)
        self.assertEqual(rarity_6_total, 1)
        self.assertEqual(rarity_7_total, 1)
        self.assertEqual(surprize_prize_total, 76)
        self.assertEqual(stickers.count(), total_stickers)

    def test_boxes_content(self):
        boxes = Box.objects.filter(edition=self.edition).order_by('pk')

        # self.assertIn(boxes[0].packs.count(), [100, 48])
        # self.assertIn(boxes[1].packs.count(), [100, 48])

        for each_box in boxes:
            self.assertEqual(str(
                each_box), f'Box N°: {each_box.id}, ordinal: {each_box.ordinal}')

# TODO: terminar esto o probarlo en otros tests


class StickerTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.edition = EditionFactory()
        cls.stickers = Sticker.objects.all().order_by('ordinal')
        cls.collectible_stickers = cls.stickers.exclude(
            coordinate__page=99)
        cls.box = cls.edition.boxes.get(edition=cls.edition)
        cls.packs = Pack.objects.filter(box__edition=cls.edition)
        # como la edition es pequeña (1 ejemplar) para fines de test, omitimos rarezas inferiores a cero
        cls.coordinates = Coordinate.objects.filter(
            collection=cls.edition.collection,
        )
        cls.common_coordinates = cls.coordinates.filter(
            rarity_factor__gte=1
        )

    def get_stickers_by_coordinate(self, coordinate_id):
        return self.stickers.filter(coordinate_id=coordinate_id).count()

    def get_stickers_by_pack(self, pack_id):
        return self.stickers.filter(pack=pack_id).count()

    def test_sticker_creation(self):
        self.assertEqual(self.stickers.count(), 45)
        self.assertEqual(self.collectible_stickers.count(), 44)

    def test_stickers_data(self):

        for each_sticker in self.stickers:
            self.assertEqual(each_sticker.box, self.box)
            self.assertEqual(str(each_sticker), str(each_sticker.number))
            self.assertEqual(each_sticker.edition, self.edition)
            self.assertEqual(each_sticker.collection, self.edition.collection)
            self.assertEqual(each_sticker.edition, self.edition)
            self.assertEqual(each_sticker.number,
                             each_sticker.coordinate.number)
            self.assertEqual(each_sticker.rarity,
                             each_sticker.coordinate.rarity_factor)
            self.assertEqual(each_sticker.page, each_sticker.coordinate.page)

        for each_coordinate in self.common_coordinates:
            self.assertEqual(self.get_stickers_by_coordinate(
                each_coordinate.id), each_coordinate.rarity_factor *
                self.edition.circulation
            )

        for each_pack in self.packs:
            self.assertLessEqual(self.get_stickers_by_pack(
                each_pack.id), self.edition.collection.STICKERS_PER_PACK)
        counter = 1
        for each_sticker in self.stickers:
            self.assertEqual(each_sticker.ordinal, counter)
            counter += 1


class BoxTextCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.edition = EditionFactory()
        cls.box = cls.edition.boxes.get(edition=cls.edition)

    def test_box_data(self):
        self.assertEqual(self.box.edition, self.edition)
        self.assertEqual(self.box.ordinal, 1)
        self.assertEqual(Box.objects.all().count(), 1)
        self.assertEqual(
            str(self.box), f'Box N°: {self.box.id}, ordinal: {self.box.ordinal}')

# TODO: aqui fatan mas tests


class AlbumTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.album = AlbumFactory(
            collector__email="albumcollector@example.com",
            edition__collection__name="Los Simpsons"
        )

    def test_album_data(self):
        self.assertEqual(self.album.collector.email,
                         "albumcollector@example.com")
        self.assertEqual(self.album.edition.collection.name, "Los Simpsons")
        self.assertEqual(str(self.album), str(self.album.edition.collection))
        self.assertEqual(self.album.missing_stickers, 24)
        self.assertEqual(self.album.collected_stickers, 0)
