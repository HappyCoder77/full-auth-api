import factory
from datetime import datetime, date
from django.db import models
from django.utils import timezone
from editions.test.factories import EditionFactory
from authentication.test.factories import UserFactory
from promotions.test.factories import PromotionFactory
from ..models import Sale, Order, Payment, MobilePayment, DealerBalance


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
        skip_validation = kwargs.pop("skip_validation", False)
        obj = model_class(*args, **kwargs)
        if skip_validation:
            # Guardar sin llamar a full_clean
            models.Model.save(obj)
        else:
            obj.save()
        return obj


class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payment

    status = "pending"
    dealer = factory.SubFactory(UserFactory)
    date = factory.LazyFunction(timezone.now)
    payment_date = factory.LazyFunction(lambda: date.today())

    bank = "0134"  # Banesco por defecto
    amount = factory.Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
    reference = factory.Sequence(lambda n: f"REF{n:08d}")
    id_number = factory.Faker("random_number", digits=8, fix_len=True)
    capture = factory.django.ImageField(color="blue")
    payment_type = "bank"


class MobilePaymentFactory(PaymentFactory):
    class Meta:
        model = MobilePayment

    phone_code = "0414"
    phone_number = factory.Faker("random_number", digits=7, fix_len=True)
    payment_type = "mobile"


class DealerBalanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DealerBalance

    dealer = factory.SubFactory(UserFactory)
    promotion = factory.SubFactory(PromotionFactory)
    initial_balance = factory.Faker(
        "pydecimal", left_digits=4, right_digits=2, positive=True
    )
