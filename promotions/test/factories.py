import factory
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from ..models import Promotion

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
