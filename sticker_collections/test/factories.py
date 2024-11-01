import factory

from ..models import Collection


class CollectionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Collection

    name = 'Minecraft'
