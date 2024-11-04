from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import BaseProfile, RegionalManager

User = get_user_model()

SUPERUSER_EMAIL = 'superuser@example.com'
USER_EMAIL = 'user@example.com'
PASSWORD = 'password123'
USER_FIRST_NAME = "John"
USER_MIDDLE_NAME = "Joseph"
USER_LAST_NAME = "Smith"
USER_SECOND_LAST_NAME = "Brown"
USER_BIRTHDATE = '1990-01-01'


class BaseProfileTest(TestCase):
    # Crear un un usuario y un base profile de ejemplo para las pruebas
    def setUp(self):
        self.user = User.objects.create_user(
            email=USER_EMAIL, password=PASSWORD)
        self.profile = BaseProfile(
            user=self.user,
            first_name=USER_FIRST_NAME,
            middle_name=USER_MIDDLE_NAME,
            last_name=USER_LAST_NAME,
            second_last_name=USER_SECOND_LAST_NAME,
            gender='M',
            birthdate=USER_BIRTHDATE,
            email=USER_EMAIL
        )

    def test_profile_data(self):
        self.profile.save()
        self.assertEqual(self.profile.first_name, USER_FIRST_NAME)
        self.assertEqual(self.profile.middle_name, USER_MIDDLE_NAME)
        self.assertEqual(self.profile.last_name, USER_LAST_NAME)
        self.assertEqual(self.profile.second_last_name, USER_SECOND_LAST_NAME)
        self.assertEqual(self.profile.gender, 'M')
        self.assertEqual(self.profile.birthdate, USER_BIRTHDATE)
        self.assertEqual(self.profile.email, USER_EMAIL)
        self.assertTrue(self.user.has_profile())
        self.assertEqual(str(self.profile),
                         USER_FIRST_NAME + " " + USER_LAST_NAME)

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

    def test_save_profile_with_no_user(self):
        self.profile.user = None
        self.profile.full_clean()  # No debería lanzar un ValidationError
        self.profile.save()
        self.assertEqual(self.profile.user, None)

    def test_optional_middle_name(self):
        self.profile.middle_name = None
        self.profile.full_clean()  # No debería lanzar un ValidationError
        self.profile.save()
        self.assertEqual(self.profile.middle_name, None)

    def test_optional_second_last_name(self):
        self.profile.second_last_name = None
        self.profile.full_clean()  # No debería lanzar un ValidationError
        self.profile.save()
        self.assertEqual(self.profile.second_last_name, None)

    def test_optional_birthdate(self):
        self.profile.birthdate = None
        self.profile.full_clean()  # No debería lanzar un ValidationError
        self.profile.save()
        self.assertEqual(self.profile.birthdate, None)

    def test_unique_email(self):
        self.profile.save()

        with self.assertRaises(IntegrityError):
            duplicate_profile = BaseProfile(
                first_name=USER_FIRST_NAME,
                last_name=USER_LAST_NAME,
                gender="F",
                email=USER_EMAIL
            )
            duplicate_profile.save()


class RegionalManagerTest(TestCase):
    def setUp(self):
        self.creator = User.objects.create_superuser(
            email=SUPERUSER_EMAIL, password=PASSWORD)
        self.regional_manager = RegionalManager(
            first_name=USER_FIRST_NAME,
            middle_name=USER_MIDDLE_NAME,
            last_name=USER_LAST_NAME,
            second_last_name=USER_SECOND_LAST_NAME,
            gender="M",
            email=USER_EMAIL,
            created_by=self.creator
        )

    def test_regional_manager_validation(self):
        # Verificar que no se lancen errores de validación
        try:
            self.regional_manager.full_clean()
        except ValidationError as e:
            self.fail(f"full_clean() lanzó ValidationError: {e}")

    def test_create_regional_manager(self):
        self.regional_manager.save()
        saved_manager = RegionalManager.objects.get(email=USER_EMAIL)
        self.assertEqual(saved_manager.first_name, USER_FIRST_NAME)
        self.assertEqual(saved_manager.middle_name, USER_MIDDLE_NAME)
        self.assertEqual(saved_manager.last_name, USER_LAST_NAME)
        self.assertEqual(saved_manager.second_last_name,
                         USER_SECOND_LAST_NAME)
        self.assertEqual(saved_manager.gender, "M")
        self.assertEqual(saved_manager.created_by, self.creator)
        self.assertEqual(str(saved_manager),
                         USER_FIRST_NAME + " " + USER_LAST_NAME)

    def test_regional_manager_links_to_user(self):
        self.regional_manager.save()

        user = User.objects.create_user(
            email=USER_EMAIL, password=PASSWORD)
        user.refresh_from_db()
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_regionalmanager)
        self.assertFalse(user.is_localmanager)
        self.assertFalse(user.is_sponsor)
        self.assertFalse(user.is_dealer)
        self.assertFalse(user.is_collector)
