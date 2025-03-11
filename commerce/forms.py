from django import forms
from .models import Order, Box
from editions.models import Edition
from promotions.models import Promotion


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = "__all__"
        exclude = ("pack_cost",)

    def __init__(self, *args, **kwargs):  # pragma: no cover
        super().__init__(*args, **kwargs)
        current_promotion = Promotion.objects.get_current
        if current_promotion:
            self.fields["edition"].queryset = Edition.objects.filter(
                promotion=current_promotion
            )
        else:
            self.fields["edition"].queryset = Edition.objects.none()
        self.fields["box"].queryset = Box.objects.none()
