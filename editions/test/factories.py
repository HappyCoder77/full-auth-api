import factory

from collection_manager.test.factories import CollectionFactory
from promotions.test.factories import PromotionFactory
from ..models import Edition


class EditionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Edition

    collection = factory.SubFactory(CollectionFactory)
    circulation = 1
