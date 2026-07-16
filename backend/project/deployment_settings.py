import dj_database_url
from .settings import *
from decouple import config
import os

ALLOWED_HOSTS = config("PROD_ALLOWED_HOST")
CSRF_TRUSTED_ORIGINS = [f"https://{config('PROD_ALLOWED_HOST')}"]
DEBUG=False
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
        conn_max_age=600
    )
}