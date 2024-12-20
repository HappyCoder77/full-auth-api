from django import forms
from .models import Order, Box
from editions.models import Edition
from promotions.utils import get_current_promotion


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_promotion = get_current_promotion()
        if current_promotion:
            self.fields["edition"].queryset = Edition.objects.filter(
                promotion=current_promotion
            )
        else:
            self.fields["edition"].queryset = Edition.objects.none()
        self.fields["box"].queryset = Box.objects.none()
