
from ..models import LocalManager, RegionalManager, Sponsor
import factory
import random
from faker import Faker
faker = Faker('es-ES')


class RegionalManagerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RegionalManager

    first_name = factory.LazyAttribute(lambda _: faker.first_name())
    last_name = factory.LazyAttribute(lambda _: faker.last_name())
    gender = 'F' if random.random() * 2 < 1 else 'M'
    email = factory.LazyAttribute(lambda _: faker.unique.email())


class LocalManagerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LocalManager

    first_name = factory.LazyAttribute(lambda _: faker.first_name())
    last_name = factory.LazyAttribute(lambda _: faker.last_name())
    gender = 'F' if random.random() * 2 < 1 else 'M'
    email = factory.LazyAttribute(lambda _: faker.unique.email())


class SponsorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Sponsor

    first_name = factory.LazyAttribute(lambda _: faker.first_name())
    last_name = factory.LazyAttribute(lambda _: faker.last_name())
    gender = 'F' if random.random() * 2 < 1 else 'M'
    email = factory.LazyAttribute(lambda _: faker.unique.email())
