import dj_database_url
from .base_settings import *
from decouple import config
import os

ALLOWED_HOSTS = config("PROD_ALLOWED_HOST").split(",")
CSRF_TRUSTED_ORIGINS = [f"https://{config('PROD_ALLOWED_HOST')}"]
DEBUG=False
SILKY_PYTHON_PROFILER = False
SECRET_KEY = config('PROD_SECRET_KEY')

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "silk.middleware.SilkyMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

# CORS_ALLOWED_ORIGINS = []

STORAGES = {
    "default":{
        "BACKEND":"django.core.files.storage.FileSystemStorage",
    },
    "staticfiles":{
        "BACKEND":"whitenoise.storage.CompressedStaticFilesStorage",
    }
}

DATABASES = {
    "default": dj_database_url.config(
        default=config("PROD_DATABASE_URL"),
        engine="django.contrib.gis.db.backends.postgis",
        conn_max_age=600,
    )
}

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("JWT",),
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}

GDAL_LIBRARY_PATH = config("GDAL_LIBRARY_PATH")
PROJ_LIB = config("PROJ_LIB")

