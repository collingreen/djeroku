web: uwsgi uwsgi.ini
scheduler: python manage.py celery worker -B -E --concurrency=2 --maxtasksperchild=1000
worker: python manage.py celery worker -E --concurrency=2 --maxtasksperchild=1000
multiworker: python manage.py celery worker -E --concurrency=2 --maxtasksperchild=1000
