import factory

from collection_manager.test.factories import CollectionFactory
from authentication.test.factories import UserFactory
from ..models import Album


class AlbumFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Album

    collector = factory.SubFactory(UserFactory)
    collection = factory.SubFactory(CollectionFactory)
