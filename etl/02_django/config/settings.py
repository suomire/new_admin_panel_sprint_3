from pathlib import Path
from split_settings.tools import include
import os
from dotenv import load_dotenv


load_dotenv("config/.env")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', False) == 'True'

ROOT_URLCONF = 'config.urls'

WSGI_APPLICATION = 'config.wsgi.application'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

include(
    'components/database.py',
    'components/language.py',
    'components/installed_apps.py',
    'components/middleware.py',
    'components/auth.py',
    'components/templates.py',
    'components/allowed_hosts.py',

)

# Локализация
LOCALE_PATHS = ['movies/locale']

# For Debug Toolbar
INTERNAL_IPS = os.environ.get('INTERNAL_IPS').split(" ")
