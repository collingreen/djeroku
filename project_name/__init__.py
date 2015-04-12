# load celery on init so @shared_task will use this app
from __future__ import absolute_import
from .celery_config import app as celery_app
