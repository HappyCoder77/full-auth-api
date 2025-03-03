import factory
import tempfile
from PIL import Image
from django.core.files.base import ContentFile

from promotions.test.factories import PromotionFactory
from ..models import OldCollection, Theme, Collection


class ThemeFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Theme

    name = "Minecraft"

    class Params:
        with_image = factory.Trait(
            image=factory.lazy_attribute(lambda x: create_test_image()),
        )


class OldCollectionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = OldCollection

    name = "Minecraft"

    class Params:
        with_image = factory.Trait(
            image=factory.lazy_attribute(lambda x: create_test_image()),
        )


class CollectionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Collection

    theme = factory.SubFactory(ThemeFactory)
    promotion = factory.SubFactory(PromotionFactory)


def create_test_image(filename="test_image.png"):
    image = Image.new("RGB", (100, 100), color=(255, 0, 0))
    tmp_file = tempfile.NamedTemporaryFile(suffix=".png")
    image.save(tmp_file)
    tmp_file.seek(0)
    return ContentFile(tmp_file.read(), filename)
