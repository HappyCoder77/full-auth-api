import factory

from editions.test.factories import EditionFactory
from authentication.test.factories import UserFactory
from ..models import Album


class AlbumFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Album

    collector = factory.SubFactory(UserFactory)
    edition = factory.SubFactory(EditionFactory)
