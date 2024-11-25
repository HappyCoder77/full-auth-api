import factory
import tempfile
from PIL import Image
from django.core.files.base import ContentFile

from ..models import Collection, Coordinate


class CollectionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Collection

    name = 'Minecraft'

    class Params:
        with_image = factory.Trait(
            image=factory.lazy_attribute(lambda x: create_temp_image()),
        )


def create_temp_image():
    image = Image.new('RGB', (100, 100), color=(255, 0, 0))
    tmp_file = tempfile.NamedTemporaryFile(suffix='.png')
    image.save(tmp_file)
    tmp_file.seek(0)
    return ContentFile(tmp_file.read(), 'collection_image.png')
