import os
from celery import Celery
import logging

logger = logging.getLogger(__name__)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "full_auth.settings")

app = Celery("full_auth")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
