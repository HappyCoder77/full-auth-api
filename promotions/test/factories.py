import factory
from datetime import timedelta
from django.utils import timezone
from ..models import Promotion


class PromotionFactory(factory.django.DjangoModelFactory):
    envelope_cost = 1.5

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

        one_hour_before_and_after = factory.Trait(
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(hours=1),
        )
