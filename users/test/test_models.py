from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.contrib.auth import get_user_model
from users.models import BaseProfile
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
        self.assertTrue(self.user.check_password(self.USER_PASSWORD))
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


class UserAccountTests(TestCase):
    USER_EMAIL = 'user@example.com'
    USER_PASSWORD = 'password123'

    # Crear un un usuario de ejemplo para las pruebas
    def setUp(self):
        self.user = User.objects.create_user(
            email=self.USER_EMAIL, password=self.USER_PASSWORD)

    def test_user_data(self):
        self.assertEqual(self.user.email, self.USER_EMAIL)
        self.assertNotEqual(self.user.password, self.USER_PASSWORD)
        self.assertTrue(self.user.check_password(self.USER_PASSWORD))
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
        self.assertTrue(self.user.is_collector)

    def test_user_str(self):
        self.assertEqual(str(self.user), self.USER_EMAIL)

    def test_is_regionalmanager(self):
        self.assertFalse(self.user.is_regionalmanager())

    def test_is_localmanager(self):
        self.assertFalse(self.user.is_localmanager())

    def test_is_sponsor(self):
        self.assertFalse(self.user.is_sponsor())

    def test_is_dealer(self):
        self.assertFalse(self.user.is_dealer())

    def test_has_profile(self):
        self.assertFalse(self.user.has_profile())


class BaseProfileTest(TestCase):
    USER_EMAIL = 'user@example.com'
    USER_PASSWORD = 'password123'
    USER_FIRST_NAME = "John"
    USER_MIDDLE_NAME = "Joseph"
    USER_LAST_NAME = "Smith"
    USER_SECOND_LAST_NAME = "Brown"
    USER_BIRTHDATE = '1990-01-01'

    # Crear un un usuario y un base profile de ejemplo para las pruebas
    def setUp(self):
        self.user = User.objects.create_user(
            email=self.USER_EMAIL, password=self.USER_PASSWORD)
        self.profile = BaseProfile.objects.create(
            user=self.user,
            first_name=self.USER_FIRST_NAME,
            middle_name=self.USER_MIDDLE_NAME,
            last_name=self.USER_LAST_NAME,
            second_last_name=self.USER_SECOND_LAST_NAME,
            gender='M',
            birthdate=self.USER_BIRTHDATE,
            email=self.USER_EMAIL
        )

    def test_profile_data_with_user(self):
        self.assertEqual(self.profile.first_name, self.USER_FIRST_NAME)
        self.assertEqual(self.profile.middle_name, self.USER_MIDDLE_NAME)
        self.assertEqual(self.profile.last_name, self.USER_LAST_NAME)
        self.assertEqual(self.profile.second_last_name,
                         self.USER_SECOND_LAST_NAME)
        self.assertEqual(self.profile.gender, 'M')
        self.assertEqual(self.profile.birthdate, self.USER_BIRTHDATE)
        self.assertEqual(self.profile.email, self.USER_EMAIL)
        self.assertTrue(self.user.has_profile())
        self.assertEqual(str(self.profile),
                         self.USER_FIRST_NAME + " " + self.USER_LAST_NAME)

    def test_required_fields(self):
        profile = BaseProfile(
            first_name="",
            last_name="",
            gender="",
            email=""
        )
        with self.assertRaises(ValidationError):
            profile.full_clean()  # Esto lanzará la ValidationError
            profile.save()  # Esto no debería ejecutarse

    def test_none_user(self):
        profile = BaseProfile(
            first_name=self.USER_FIRST_NAME,
            last_name=self.USER_LAST_NAME,
            gender="M",
            email="john.doe@example.com"
        )
        profile.full_clean()  # No debería lanzar un ValidationError
        profile.save()
        self.assertEqual(profile.user, None)

    def test_optional_middle_name(self):
        profile = BaseProfile(
            first_name=self.USER_FIRST_NAME,
            last_name=self.USER_LAST_NAME,
            gender="M",
            email="john.doe1@example.com"
        )
        profile.full_clean()  # No debería lanzar un ValidationError
        profile.save()
        self.assertEqual(profile.middle_name, None)

    def test_optional_second_last_name(self):
        profile = BaseProfile(
            first_name=self.USER_FIRST_NAME,
            last_name=self.USER_LAST_NAME,
            gender="M",
            email="john.doe2@example.com"
        )
        profile.full_clean()  # No debería lanzar un ValidationError
        profile.save()
        self.assertEqual(profile.second_last_name, None)

    def test_optional_birthdate(self):
        profile = BaseProfile(
            first_name="John",
            last_name="Doe",
            gender="M",
            email="john.doe@example.com"
        )
        profile.full_clean()  # No debería lanzar un ValidationError
        profile.save()
        self.assertEqual(profile.birthdate, None)

    def test_unique_email(self):
        BaseProfile.objects.create(

            first_name="John",
            last_name="Doe",
            gender="M",
            email="john.doe@example.com"
        )
        with self.assertRaises(IntegrityError):
            duplicate_profile = BaseProfile(
                first_name=self.USER_FIRST_NAME,
                last_name=self.USER_LAST_NAME,
                gender="F",
                email="john.doe@example.com"
            )
            duplicate_profile.save()
