import dj_database_url
from .base_settings import *
from decouple import config
import os

ALLOWED_HOSTS = config("PROD_ALLOWED_HOST").split(",")
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS if host]
DEBUG=False
SILKY_PYTHON_PROFILER = False
SECRET_KEY = config('PROD_SECRET_KEY')

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "silk.middleware.SilkyMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

CORS_ALLOWED_ORIGINS = config("PROD_CORS_ALLOWED_ORIGIN").split(",")

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
        conn_max_age=0,
    )
}
DOMAIN = config("CLIENT-DOMAIN")
EMAIL_BACKEND = config("EMAIL_BACKEND")
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL")
EMAIL_PORT = config("EMAIL_PORT")
EMAIL_USE_TLS = config("EMAIL_USE_TLS",cast=bool)

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("JWT",),
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}

GDAL_LIBRARY_PATH = config("GDAL_LIBRARY_PATH")
PROJ_LIB = config("PROJ_LIB")

