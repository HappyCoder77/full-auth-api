from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import UserAccount


class UserAccountCreationForm(UserCreationForm):

    class Meta:
        model = UserAccount
        fields = ("email", "password1", "password2")


class UserAccountChangeForm(UserChangeForm):

    class Meta:
        model = UserAccount
        fields = ("email",)
