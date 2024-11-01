import factory

from sticker_collections.test.factories import CollectionFactory
from ..models import Edition


class EditionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Edition

    collection = factory.SubFactory(CollectionFactory)
    circulation = 1
