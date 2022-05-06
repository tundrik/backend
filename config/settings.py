from pathlib import Path

from constants import DATABASE_USER, DATABASE_PASSWORD, SECRET_KEY, DATABASE_HOST, DEBUG

DEBUG = DEBUG

FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760

SECRET_KEY = SECRET_KEY

BASE_DIR = Path(__file__).resolve().parent.parent

ROOT_URLCONF = 'api.urls'

INSTALLED_APPS = [
    'django.contrib.postgres',
    'domain',
]

MIDDLEWARE = [
    'config.middleware.ResponseHttpMiddleware'
]

DATABASES = {
    'default': {
        'CONN_MAX_AGE': 5,
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'graph',
        'USER': DATABASE_USER,
        'PASSWORD': DATABASE_PASSWORD,
        'HOST': DATABASE_HOST,
        'PORT': '5432',
        'ATOMIC_REQUESTS': False,
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'Europe/Moscow'

DATE_FORMAT = '%m/%d/%Y'

USE_I18N = True

USE_L10N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
