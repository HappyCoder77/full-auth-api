import factory
from datetime import timedelta
from django.utils import timezone
from ..models import Promotion, Collection, Edition


class PromotionFactory(factory.django.DjangoModelFactory):
    pack_cost = 1.5

    class Meta:
        model = Promotion

    class Params:
        now = timezone.now()
        past = factory.Trait(
            start_date=now - timedelta(days=3),
            end_date=now - timedelta(days=2),
        )

        future = factory.Trait(
            start_date=now + timedelta(days=2),
            end_date=now + timedelta(days=2),
        )


class CollectionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Collection

    name = 'Minecraft'


class EditionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Edition

    promotion = factory.SubFactory(PromotionFactory)
    collection = factory.SubFactory(CollectionFactory)
    circulation = 1
