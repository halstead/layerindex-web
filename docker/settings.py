# Django settings for layerindex project.
#
# Based on settings.py from the Django project template
# Copyright (c) Django Software Foundation and individual contributors.

import os

DEBUG = os.getenv('DEBUG', False)

ADMINS = (
    ('Paul Eggleton', 'paul.eggleton@linux.intel.com'),
    ('Michael Halstead', 'mhalstead@linuxfoundation.org'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'layersdb',
        'USER': 'root',
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'testingpw'),
        'HOST': os.getenv('DATABASE_HOST', 'layersdb'),
        'PORT': '',
    }
}

TIME_ZONE = 'Etc/UTC'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = True

USE_L10N = True

BASE_DIR = os.path.dirname(__file__)

MEDIA_ROOT = ''

MEDIA_URL = ''

STATIC_ROOT = '/usr/share/nginx/html/static/'

STATIC_URL = '/static/'

ADMIN_MEDIA_PREFIX = '/static/admin/'

STATICFILES_DIRS = (
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

SECRET_KEY = os.getenv('SECRET_KEY', 'aabbccddee1122334455')

MIDDLEWARE_CLASSES = (
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'reversion.middleware.RevisionMiddleware',
)

CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r'.*/api/.*';

X_FRAME_OPTIONS = 'DENY'

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR + "/templates",
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
                'layerindex.context_processors.layerindex_context',
            ],
        },
    },
]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'layerindex',
    'registration',
    'reversion',
    'reversion_compare',
    'captcha',
    'rest_framework',
    'corsheaders',
    'django_nvd3'
)

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'layerindex.restperm.ReadOnlyPermission',
    ),
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%m:%S+0000',
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.SUCCESS: 'alert-success',
    messages.INFO: 'alert-info',
    messages.WARNING: '',
    messages.ERROR: 'alert-error',
}

# Registration settings
ACCOUNT_ACTIVATION_DAYS = 2
EMAIL_HOST = os.getenv('EMAIL_HOST', 'layers.test')
DEFAULT_FROM_EMAIL = 'noreply@' + os.getenv('HOSTNAME', 'layers.test')
LOGIN_REDIRECT_URL = '/layerindex'

# Full path to directory where layers should be fetched into by the update script
LAYER_FETCH_DIR = "/opt/workdir"

# Base temporary directory in which to create a directory in which to run BitBake
TEMP_BASE_DIR = "/tmp"

# Fetch URL of the BitBake repository for the update script
BITBAKE_REPO_URL = "git://git.openembedded.org/bitbake"

# Core layer to be used by the update script for basic BitBake configuration
CORE_LAYER_NAME = "openembedded-core"

# Update records older than this number of days will be deleted every update
UPDATE_PURGE_DAYS = 30

# Remove layer dependencies that are not specified in conf/layer.conf
REMOVE_LAYER_DEPENDENCIES = False

# Always use https:// for review URLs in emails (since it may be redirected to
# the login page)
FORCE_REVIEW_HTTPS = True

# Settings for layer submission feature
SUBMIT_EMAIL_FROM = 'noreply@' + os.getenv('HOSTNAME', 'layers.test')
SUBMIT_EMAIL_SUBJECT = 'OE Layerindex layer submission'

# RabbitMQ settings
PARALLEL_JOBS = "4"
RABBIT_BROKER = 'amqp://guest:guest@layersrabbit:5672/'
RABBIT_BACKEND = 'rpc://layersrabbit/'

USE_X_FORWARDED_HOST = True
ALLOWED_HOSTS = [os.getenv('HOSTNAME', 'layers.test')]
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

