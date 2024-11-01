from django.test import TestCase

from promotions.test.factories import PromotionFactory

from .factories import AlbumFactory
# TODO: aqui fatan mas tests


class AlbumTestCase(TestCase):
    @ classmethod
    def setUpTestData(cls):
        promotion = PromotionFactory()
        cls.album = AlbumFactory(
            collector__email="albumcollector@example.com",
            edition__promotion=promotion,
            edition__collection__name="Los Simpsons"
        )

    def test_album_data(self):
        self.assertEqual(self.album.collector.email,
                         "albumcollector@example.com")
        self.assertEqual(self.album.edition.collection.name, "Los Simpsons")
        self.assertEqual(str(self.album), str(self.album.edition.collection))
        self.assertEqual(self.album.missing_stickers, 24)
        self.assertEqual(self.album.collected_stickers, 0)
