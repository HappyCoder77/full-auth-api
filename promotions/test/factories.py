import factory
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from ..models import (Promotion, Collection, Edition, Sticker, Album)
from users.models import UserAccount

User = get_user_model()


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


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserAccount

    email = factory.Faker("email")


class AlbumFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Album

    collector = factory.SubFactory(UserFactory)
    edition = factory.SubFactory(EditionFactory)
