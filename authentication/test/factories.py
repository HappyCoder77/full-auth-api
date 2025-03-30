import factory


from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Faker("email")

    class Params:
        active = factory.Trait(is_active=True)

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """
        Handle password hashing
        """
        if not create:
            # Simple build, do nothing
            return

        # A password was specified
        if extracted:
            self.set_password(extracted)
            self.save()
