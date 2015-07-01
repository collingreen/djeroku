# load celery on init so @shared_task will use this app
from __future__ import absolute_import
from .celery import app as celery_app  # NOQA
