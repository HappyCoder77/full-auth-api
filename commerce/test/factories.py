import factory

from editions.test.factories import EditionFactory
from authentication.test.factories import UserFactory
from ..models import Sale, Order


class SaleFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Sale
    dealer = factory.SubFactory(UserFactory)
    quantity = 1


class Orderfactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Order

    dealer = factory.SubFactory(UserFactory)
