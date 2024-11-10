from django.conf import settings
from storages.backends.s3 import S3Storage

class CustomS3Storage(S3Storage):
    location = settings.AWS_MEDIA_LOCATION