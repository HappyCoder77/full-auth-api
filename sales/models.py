from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from albums.models import Pack
from editions.models import Edition

User = get_user_model()


class Sale(models.Model):
    """
    Sale de packs al collector.
    Los atributos edition, collector y quantity no cumplen estrictamente con la normalización
    ya que no conciernen estrictamente a la sale sino a los packs,
    pero la experiencia demostró que facilita las consultas y otras operaciones pack el modelo.
    Esto se bede a la política de vender packs de solo una collection por sale
    """
    date = models.DateField(default=timezone.now)
    edition = models.ForeignKey(
        Edition, on_delete=models.CASCADE, related_name='sales', null=True)
    dealer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sales',
        null=True
    )

    collector = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='purchases',
        null=True
    )

    quantity = models.SmallIntegerField()

    def __str__(self):
        return f'{self.id} / {self.date} / {self.collector}'

    @property
    def collection(self):
        return self.edition.collection

    def clean(self):
        """
        se consultan los packs en el insalerio del dealer
        para saber si hay suficientes para la sale, en caso contrario se genera
        error de validación
        """

        available_packs = Pack.objects.filter(
            sale__isnull=True,
            box__edition=self.edition,
            box__purchase__dealer=self.dealer
        ).order_by('ordinal').count()

        if available_packs < self.quantity:

            raise ValidationError(
                f'Inventario insuficiente: quedan {available_packs} sobres disponibles en inventario'
            )

    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        Para relacionar los sobres correspondientes a a la venta actual
        y actualizar las opciones de rescate
        """
        super(Sale, self).save(*args, **kwargs)
        available_packs = Pack.objects.filter(
            sale__isnull=True,
            box__edition=self.edition,
            box__purchase__dealer=self.dealer
        ).order_by('ordinal')[:self.quantity]

        pack_list = []

        for each_pack in available_packs:
            each_pack.sale = self
            pack_list.append(each_pack)

        Pack.objects.bulk_update(pack_list, ['sale'])
        self.collector.rescue_options += self.quantity
        self.collector.save(update_fields=['rescue_options'])
