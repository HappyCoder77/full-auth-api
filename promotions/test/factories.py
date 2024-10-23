import factory
from ..models import Promotion


class PromotionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Promotion

    duration = 90
    envelope_cost = 1.5
