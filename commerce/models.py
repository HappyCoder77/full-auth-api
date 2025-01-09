from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import (
    RegexValidator,
    FileExtensionValidator,
)
from django.db import models, transaction
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.utils import timezone

from editions.models import Edition, Box, Pack
from promotions.models import Promotion
from promotions.utils import promotion_is_running
from editions.utils import get_current_editions

User = get_user_model()


class Sale(models.Model):
    """
    Sale de packs al collector.
    Los atributos edition, collector y quantity no cumplen estrictamente con la normalización
    ya que no conciernen estrictamente a la sale sino a los packs,
    pero la experiencia demostró que facilita las consultas y otras operaciones pack el modelo.
    Esto se debe a la política de vender packs de solo una collection por sale
    """

    date = models.DateField(default=timezone.now)
    edition = models.ForeignKey(
        Edition, on_delete=models.CASCADE, related_name="sales", null=True
    )
    dealer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sales", null=True
    )

    collector = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="purchases", null=True
    )

    quantity = models.SmallIntegerField()

    def __str__(self):
        return f"{self.id} / {self.date} / {self.collector}"

    @property
    def collection(self):
        return self.edition.collection

    def clean(self):
        """
        se consultan los packs en el inventario del dealer
        para saber si hay suficientes para la venta, en caso contrario se genera
        error de validación
        """

        available_packs = (
            Pack.objects.filter(
                sale__isnull=True,
                box__edition=self.edition,
                box__order__dealer=self.dealer,
            )
            .order_by("ordinal")
            .count()
        )
        if available_packs < self.quantity:

            raise ValidationError(
                f"Inventario insuficiente: quedan {available_packs} packs disponibles en inventario"
            )

    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        Para relacionar los Packs correspondientes a a la venta actual
        y actualizar las opciones de rescate
        """
        super(Sale, self).save(*args, **kwargs)
        available_packs = Pack.objects.filter(
            sale__isnull=True, box__edition=self.edition, box__order__dealer=self.dealer
        ).order_by("ordinal")[: self.quantity]

        # pack_list = []

        for each_pack in available_packs:
            SaleDetail.objects.create(sale=self, pack=each_pack)

        # self.collector.rescue_options += self.quantity
        # self.collector.save(update_fields=['rescue_options'])

        # each_pack.sale = self
        # pack_list.append(each_pack)

        # Pack.objects.bulk_update(pack_list, ['sale'])


class SaleDetail(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="packs")
    pack = models.OneToOneField(
        Pack, on_delete=models.SET_NULL, null=True, related_name="sale"
    )


class Order(models.Model):
    dealer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    date = models.DateField(default=timezone.now)
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE, null=True)
    box = models.OneToOneField(Box, on_delete=models.CASCADE, null=True, blank=True)
    pack_cost = models.DecimalField(
        verbose_name="costo unitario del sobre",
        decimal_places=2,
        max_digits=4,
        default=0,
    )

    def __str__(self):
        return f"{self.id} / {self.date}"

    @property
    def amount(self):
        packs = Pack.objects.filter(box__order=self).count()
        amount = packs * self.pack_cost
        return amount

    def clean(self):
        if not promotion_is_running():
            raise ValidationError(
                "No hay ninguna promoción en curso; no se puede realizar esta acción"
            )
        if not get_current_editions():
            raise ValidationError(
                "No hay ninguna edición en curso; no se puede realizar esta acción"
            )

        if not Edition.objects.filter(pk=self.edition_id).exists():
            raise ValidationError("No existe ninguna edición con el id suministrado")

        current_pack_stock = self.dealer.baseprofile.dealer.get_pack_stock(
            edition_id=self.edition_id
        )

        dealer_balance = (
            DealerBalance.objects.filter(dealer=self.dealer, promotion__isnull=False)
            .order_by("-start_date")
            .first()
        )

        if dealer_balance and dealer_balance.current_balance > 0:
            raise ValidationError(
                "No puedes realizar nuevas compras mientras tengas saldo pendiente"
            )

        if current_pack_stock > 0:
            raise ValidationError(
                "No puedes comprar mas sobres mientras tengas inventario disponible"
            )

        box = Box.objects.filter(edition=self.edition, order__isnull=True).first()

        if not box:
            raise ValidationError(f"No hay paquetes disponibles para esta edición")

        self.box = box
        self.pack_cost = self.box.edition.promotion.pack_cost

    @transaction.atomic
    def save(self, *args, **kwargs):
        if not self.pk:
            self.full_clean()
        super(Order, self).save(*args, **kwargs)

    @classmethod
    def create(cls, **kwargs):
        # Asegurarse de que 'box' no está en los datos, incluso si alguien intenta incluirlo
        kwargs.pop("box", None)
        instance = cls(**kwargs)
        instance.save()
        return instance


class Payment(models.Model):
    PAYMENT_STATUS = [
        ("pending", "Pendiente"),
        ("completed", "Completado"),
        ("rejected", "Rechazado"),
    ]

    BANKS = [
        ("0102", "Banco de Venezuela"),
        ("0104", "Venezolano de Crédito"),
        ("0105", "Banco Mercantil"),
        ("0108", "BBVA Provincial"),
        ("0114", "Bancaribe"),
        ("0115", "Banco Exterior"),
        ("0116", "Banco Occidental de Descuento"),
        ("0128", "Banco Caroní"),
        ("0134", "Banesco"),
        ("0137", "Banco Sofitasa"),
        ("0138", "Banco Plaza"),
        ("0146", "Bangente"),
        ("0151", "BFC Banco Fondo Común"),
        ("0156", "100% Banco"),
        ("0157", "DelSur"),
        ("0163", "Banco del Tesoro"),
        ("0166", "Banco Agrícola de Venezuela"),
        ("0168", "Bancrecer"),
        ("0169", "Mi Banco"),
        ("0171", "Banco Activo"),
        ("0172", "Bancamiga"),
        ("0174", "Banplus"),
        ("0175", "Banco Bicentenario"),
        ("0177", "Banfanb"),
        ("0178", "N58 Banco Digital"),
        ("0191", "Banco Nacional de Crédito"),
    ]

    PAYMENT_TYPES = [
        ("bank", "Transferencia Bancaria"),
        ("mobile", "Pago Móvil"),
    ]

    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default="pending")
    dealer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    date = models.DateTimeField(default=timezone.now, db_index=True)
    payment_date = models.DateField()
    bank = models.CharField(max_length=4, choices=BANKS)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    reference = models.CharField(
        max_length=20,
        unique=True,
        error_messages={
            "unique": "La referencia del pago ya existe",
        },
    )
    id_number = models.CharField(
        max_length=8,
        help_text="Cédula del titular de la cuenta (sin letra inicial, guiones ni puntos)",
        validators=[
            RegexValidator(
                r"^\d{7,8}$", "Ingrese un número de cédula válido (6 hasta 8 dígitos)"
            )
        ],
    )
    capture = models.ImageField(
        upload_to="captures/payments",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg", "jpeg", "png"],
                message="Solo se permiten archivos de imagen (jpg, jpeg, png)",
            )
        ],
    )
    payment_type = models.CharField(max_length=6, choices=PAYMENT_TYPES, default="bank")

    def __str__(self) -> str:
        return (
            f"{self.dealer.email} - {self.amount} - {self.payment_date} - {self.status}"
        )

    def save(self, *args, **kwargs):
        self.amount = Decimal(str(self.amount)).quantize(Decimal("0.01"))
        status_changed = False
        if not self.pk:
            # Enforce default status value on creation
            self.status = "pending"
        else:
            # Only if the field status has changed the signal will be triggered
            old_payment = Payment.objects.get(pk=self.pk)
            if old_payment.status != self.status:
                status_changed = True
        super().save(*args, **kwargs)
        if status_changed:
            self.handle_status_change()

    def handle_status_change(self):
        # Determine balances to update
        affected_balances = DealerBalance.objects.filter(
            dealer=self.dealer,
            start_date__gte=self.payment_date,
        ).order_by("start_date")

        for idx, balance in enumerate(affected_balances):
            balance.refresh_from_db()
            current_balance = balance.current_balance

            if idx < len(affected_balances) - 1:
                next_balance = affected_balances[idx + 1]
                next_balance.initial_balance = current_balance
                next_balance.save()


@receiver(post_delete, sender=Payment)
def handle_payment_delete(sender, instance, **kwargs):
    if instance.status == "completed":
        instance.handle_status_change()


class MobilePayment(Payment):
    PHONE_CODES = [
        ("0412", "0412"),
        ("0414", "0414"),
        ("0416", "0416"),
        ("0424", "0424"),
        ("0426", "0426"),
    ]
    phone_code = models.CharField(max_length=4, choices=PHONE_CODES)
    phone_number = models.CharField(
        max_length=7,
        validators=[
            RegexValidator(
                r"^\d{7}$", "Ingrese un número de teléfono válido (7 dígitos)"
            )
        ],
    )

    def save(self, *args, **kwargs):
        self.payment_type = "mobile"
        super().save(*args, **kwargs)


class DealerBalance(models.Model):
    dealer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="promotion_balances"
    )
    promotion = models.ForeignKey(
        Promotion,
        on_delete=models.CASCADE,
        related_name="balances",
        null=True,
        blank=True,
    )
    initial_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["dealer", "promotion"]

    """la fecha final es un dia despues de la fecha final de la promocion
    para evitar fallos en casos extremos como promociones
    de un dia consecutivas"""

    def __str__(self):
        promotion_date = self.promotion.end_date.date() if self.promotion else "*"
        return f"{self.dealer.email} - {self.start_date} - {promotion_date}"

    @property
    def end_date(self):

        if self.promotion:
            return self.promotion.end_date.date() + timedelta(days=1)

        return None

    @property
    def payments_total(self):
        filters = {
            "dealer": self.dealer,
            "payment_date__gte": self.start_date,
            "status": "completed",
        }

        if self.end_date:
            filters["payment_date__lt"] = self.end_date

        result = Payment.objects.filter(**filters).aggregate(
            total=models.Sum("amount")
        )["total"] or Decimal("0.00")

        return result

    @property
    def orders_total(self):
        if not self.promotion:
            return Decimal("0.00")
        return sum(
            order.amount
            for order in Order.objects.filter(
                dealer=self.dealer,
                date__range=(self.promotion.start_date, self.promotion.end_date),
            )
        )

    @property
    def current_balance(self):
        return self.initial_balance + self.orders_total - self.payments_total
