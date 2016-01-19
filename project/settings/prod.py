"""
Production settings

Debug OFF

Djeroku Defaults:
    Mailgun Email -- Requires Mailgun addon
    dj_database_url and django-postgrespool for heroku postgres configuration
    memcachify for heroku memcache configuration
    Commented out by default - redisify for heroku redis cache configuration

What you need to set in your heroku environment (heroku config:set key=value):

    ALLOWED_HOSTS - You MUST add your site urls here if they don't match
    the included defaults. If you have trouble, try prepending your url with
    a . - eg: '.yourproject.herokuapp.com'.

    Optional - Update your production environment SECRET_KEY (created and set
    automatically by during project creation by the djeroku setup)

    Email:
        Defaults to mailgun, which is already set up when added to your app

        There is also a commented version that uses your gmail address.
        For more control, you can set any of the following keys in your
        environment:
        EMAIL_HOST, EMAIL_HOST_PASSWORD, EMAIL_HOST_USER, EMAIL_PORT
"""

from os import environ

import dj_database_url

# automagically sets up whatever memcache heroku addon you have as the cache
# https://github.com/rdegges/django-heroku-memcacheify
from memcacheify import memcacheify

# use redisify instead of memcacheify if you prefer
# https://github.com/dirn/django-heroku-redisify
# from redisify import redisify

from project.settings.common import *  # NOQA


# ALLOWED HOSTS
# https://docs.djangoproject.com/en/1.8/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [
    '.{{ project_name }}.herokuapp.com',
    '.{{ project_name}}-staging.herokuapp.com'
]
# you MUST add your domain names here, check the link for details
# END ALLOWED HOSTS


# EMAIL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-host
# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-host-password
# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-host-user
# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-port
# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-use-tls

EMAIL_HOST = environ.get('MAILGUN_SMTP_SERVER', 'smtp.mailgun.com')
EMAIL_HOST_PASSWORD = environ.get('MAILGUN_SMTP_PASSWORD', '')
EMAIL_HOST_USER = environ.get('MAILGUN_SMTP_LOGIN', '')
EMAIL_PORT = environ.get('MAILGUN_SMTP_PORT', 587)
EMAIL_USE_TLS = True

# use this to channel your emails through a gmail powered account instead
# EMAIL_HOST = environ.get('EMAIL_HOST', 'smtp.gmail.com')
# EMAIL_HOST_USER = environ.get('EMAIL_HOST_USER', 'your_email@gmail.com')
# EMAIL_HOST_PASSWORD = environ.get('EMAIL_HOST_PASSWORD', '')
# EMAIL_PORT = environ.get('EMAIL_PORT', 587)
# EMAIL_USE_TLS = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
EMAIL_SUBJECT_PREFIX = '[%s] ' % SITE_NAME

# See: https://docs.djangoproject.com/en/dev/ref/settings/#server-email
SERVER_EMAIL = EMAIL_HOST_USER
# END EMAIL CONFIGURATION


# DATABASE CONFIGURATION
DATABASES['default'] = dj_database_url.config()
DATABASES['default']['ENGINE'] = 'django_postgrespool'
# END DATABASE CONFIGURATION


# CACHE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = memcacheify()
# CACHES = redisify()
# END CACHE CONFIGURATION

# Simplest redis-based config possible
# *very* easy to overload free redis/MQ connection limits
# You MUST update REDIS_SERVER_URL or use djeroku_redis to set it automatically
BROKER_POOL_LIMIT = 0
BROKER_URL = environ.get('REDIS_SERVER_URL')
CELERY_IGNORE_RESULT = True
CELERY_STORE_ERRORS_EVEN_IF_IGNORED = True
# END CELERY CONFIGURATION


# SECRET CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = environ.get('SECRET_KEY', SECRET_KEY)
# END SECRET CONFIGURATION


# ADDITIONAL MIDDLEWARE
MIDDLEWARE_CLASSES += ()
# END ADDITIONAL MIDDLEWARE

# SSLIFY
# change to False to force all requests to use https
SSLIFY_DISABLE = environ.get('SSLIFY_DISABLE', False)
# END SSLIFY
