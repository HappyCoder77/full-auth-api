import factory
from django.db import models
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

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        skip_validation = kwargs.pop('skip_validation', False)
        obj = model_class(*args, **kwargs)
        if skip_validation:
            # Guardar sin llamar a full_clean
            models.Model.save(obj)
        else:
            obj.save()
        return obj
