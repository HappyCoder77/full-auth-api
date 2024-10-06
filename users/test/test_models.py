from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserAccountManagerTests(TestCase):
    USER_EMAIL = 'user@example.com'
    SUPERUSER_EMAIL = 'superuser@example.com'
    USER_PASSWORD = 'password123'

    # Crear un un usuario de ejemplo para las pruebas
    def setUp(self):
        self.user = User.objects.create_user(
            email=self.USER_EMAIL, password=self.USER_PASSWORD)
        self.superuser = User.objects.create_superuser(
            email=self.SUPERUSER_EMAIL, password=self.USER_PASSWORD)
    # verificar metodo get_user_model()

    def test_get_user_model_method(self):
        self.assertTrue(isinstance(self.user, get_user_model()))

    # verificar que los datos del usuario estan ok
    def test_user_data(self):
        self.assertEqual(self.user.email, self.USER_EMAIL)
        self.assertNotEqual(self.user.password, self.USER_PASSWORD)
        self.assertTrue(self.user.check_password('password123'))
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
        self.assertTrue(self.user.is_collector)

    # intentar crear un un usuario con una cadena vacia como email
    def test_create_user_no_email(self):
        with self.assertRaisesMessage(ValueError, "Para crear un usario se debe proporcionar una dirección de correo electrónico"):
            User.objects.create_user(email='', password=self.USER_PASSWORD)

    # intentar crear un un usuario sin proporcionar email
    def test_create_user_method_with_no_email(self):
        with self.assertRaises(TypeError):
            User.objects.create_user(self.USER_PASSWORD)

    # intentar crear un un usuario con una cadena vacia como password
    def test_create_user_no_password(self):
        with self.assertRaisesMessage(ValueError, "La contraseña no puede estar vacía"):
            User.objects.create_user(email='test@example.com', password='')

    # intentar crear un un usuario sin proporcionar password
    def test_create_user_method_with_no_password(self):
        with self.assertRaises(TypeError):
            User.objects.create_user("user2@example.com")

    # intentar crear un un usuario sin proporcionar los datos
    def test_create_user_method_with_no_args(self):
        with self.assertRaises(TypeError):
            User.objects.create_user()

    def test_email_unique(self):
        # Intentar crear un usuario con el mismo correo electrónico
        with self.assertRaises(Exception):
            User.objects.create_user(
                email=self.USER_EMAIL, password=self.USER_PASSWORD)

    def test_create_user_email_normalization(self):
        email = "TEST@EXAMPLE.COM"
        user = User.objects.create_user(
            email=email, password=self.USER_PASSWORD)
        self.assertEqual(user.email, "test@example.com")

    def test_create_superuser_data(self):
        self.assertEqual(self.superuser.email, self.SUPERUSER_EMAIL)
        self.assertTrue(self.superuser.check_password(self.USER_PASSWORD))
        self.assertTrue(self.superuser.is_active)
        self.assertTrue(self.superuser.is_staff)
        self.assertTrue(self.superuser.is_superuser)
        self.assertFalse(self.superuser.is_collector)
