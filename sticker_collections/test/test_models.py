from django.test import TestCase

from ..models import Collection
from .factories import CollectionFactory


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
