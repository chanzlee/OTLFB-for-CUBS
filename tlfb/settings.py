import os

import dj_database_url

APP_NAME = 'tlfb'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# BASIC DJANGO SETTINGS

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'RESETME')
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
ALLOWED_HOSTS = '*'

DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'
USE_CELERY = os.getenv('DJANGO_USE_CELERY', 'True') == 'True'

TIME_ZONE = 'America/Denver'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = False
USE_L10N = True
USE_TZ = True

EMAIL_BACKEND = os.getenv('DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
ROOT_URLCONF = APP_NAME + '.urls'
WSGI_APPLICATION = APP_NAME + '.wsgi.application'

# APP AND MIDDLEWARE SETTINGS

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
]
THIRD_PARTY_APPS = [
    'django_extensions',  # all kinds of goodness
    'raven.contrib.django.raven_compat',  # sentry-django connector
    'bootstrap4',  # bootstrap 4 support
    'bootstrap_datepicker_plus',
    'tz_detect',
    'dynamic_formsets',
]
LOCAL_APPS = [
    'tlfb.data',
]
INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + THIRD_PARTY_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django_session_timeout.middleware.SessionTimeoutMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'tz_detect.middleware.TimezoneMiddleware',
]

# DATABASES AND CACHING

DATABASES = {}
DATABASES['default'] = dj_database_url.config(conn_max_age=600,
                                              default='postgres://localhost:5434/{}'.format(APP_NAME))
SESSION_EXPIRE_SECONDS = 5400
SESSION_EXPIRE_AFTER_LAST_ACTIVITY = True
SESSION_TIMEOUT_REDIRECT = '/timeout/'

# TEMPLATES AND STATIC FILES

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'OPTIONS': {
            'debug': DEBUG,
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
if DEBUG:
    TEMPLATES[0]['OPTIONS']['loaders'] = [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# SENTRY AND LOGGING SETTINGS
RAVEN_CONFIG = {
    'dsn': os.getenv('SENTRY_DSN', ''),
    # MUST USE "heroku labs:enable runtime-dyno-metadata -a <app name>"
    'release': os.getenv('HEROKU_SLUG_COMMIT', 'DEBUG')
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # disabling this messes up default django logging
    'root': {
        'level': 'DEBUG' if DEBUG else 'INFO',
        'handlers': ['console', 'sentry'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}

# CELERY SETTINGS
REDIS_URL = os.environ.get('REDIS_URL', 'redis://')
BROKER_URL = REDIS_URL
CELERY_TASK_SERIALIZER = "json"
