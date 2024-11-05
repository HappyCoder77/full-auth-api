from django.contrib.auth.models import BaseUserManager


class UserAccountManager(BaseUserManager):
    def create_user(self, email, password, **kwargs):

        if not email:
            raise ValueError(
                "Para crear un usario se debe proporcionar una dirección de correo electrónico")

        if not password:
            raise ValueError('La contraseña no puede estar vacía')

        email = self.normalize_email(email)
        email = email.lower()

        user = self.model(
            email=email,
            **kwargs
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **kwargs):
        kwargs.update({
            "is_superuser": True,
            "is_staff": True,
        })

        user = self.create_user(
            email,
            password=password,
            **kwargs
        )

        return user
