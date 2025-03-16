import factory
import tempfile
from PIL import Image
from django.core.files.base import ContentFile

from promotions.test.factories import PromotionFactory
from ..models import Theme, Collection, AlbumTemplate


class ThemeFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Theme

    name = "Minecraft"

    class Params:
        with_image = factory.Trait(
            image=factory.lazy_attribute(lambda x: create_test_image()),
        )


class CollectionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Collection

    theme = factory.SubFactory(ThemeFactory)


class AlbumTemplateFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = AlbumTemplate

    name = "Minecraft"

    class Params:
        with_image = factory.Trait(
            image=factory.lazy_attribute(lambda x: create_test_image()),
        )
        with_coordinate_images = factory.Trait()

    @factory.post_generation
    def with_coordinate_images(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        # Wait for coordinates to be created by the model's save method
        self.refresh_from_db()

        # Add images to each coordinate
        for coordinate in self.coordinates.all():
            # Create a unique image for each coordinate
            filename = f"coordinate_{coordinate.page}_{coordinate.slot_number}.png"
            coordinate.image = create_test_image(filename)
            coordinate.save()


def create_test_image(filename="test_image.png"):
    image = Image.new("RGB", (100, 100), color=(255, 0, 0))
    tmp_file = tempfile.NamedTemporaryFile(suffix=".png")
    image.save(tmp_file)
    tmp_file.seek(0)
    return ContentFile(tmp_file.read(), filename)
