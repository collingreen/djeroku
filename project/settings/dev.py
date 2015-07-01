"""
Development settings and globals.

    Debug ON

    Console Email Backend
    SQLite as the database
    Local Memory Cache
    Debug Toolbar Enabled

    Task Queue Faked (CELERY_ALWAYS_EAGER = True)
    - Or local Redis if CELERY_ALWAYS_EAGER is set to False

    Looks for localhost redis
"""


from os.path import join, normpath

from common import *  # NOQA


# DEBUG CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# END DEBUG CONFIGURATION

# ALLOWED HOSTS
# https://docs.djangoproject.com/en/1.8/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['127.0.0.1', u'localhost']
# END ALLOWED HOSTS

# EMAIL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# END EMAIL CONFIGURATION


# DATABASE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': normpath(join(DJANGO_ROOT, 'default.db')),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}
# END DATABASE CONFIGURATION


# CACHE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
# END CACHE CONFIGURATION


# TOOLBAR CONFIGURATION
# https://github.com/django-debug-toolbar/django-debug-toolbar#installation
INSTALLED_APPS += (
    'debug_toolbar',
)
INTERNAL_IPS = ('127.0.0.1',)
MIDDLEWARE_CLASSES += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)
# END TOOLBAR CONFIGURATION


# REDIS CONFIGURATION
REDIS_SERVER_URL = environ.get('REDIS_SERVER_URL', 'localhost')
# END REDIS CONFIGURATION

# CELERY CONFIGURATION
# See: http://docs.celeryq.org/en/latest/configuration.html#celery-always-eager
# Fakes a queue and just processes tasks immediately in the same thread
CELERY_ALWAYS_EAGER = True

# With ALWAYS_EAGER false, uses a local redis server for the queue
BROKER_URL = 'redis://' + REDIS_SERVER_URL
CELERY_RESULT_BACKEND = 'redis://' + REDIS_SERVER_URL
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
# END CELERY CONFIGURATION
