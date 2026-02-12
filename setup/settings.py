import json, os, sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env', verbose=True)

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = json.loads(os.getenv('DEBUG', 'false'))
ALLOWED_HOSTS = json.loads((os.getenv('ALLOWED_HOSTS', '["*"]')))

# Application definition
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'aluguel_quadra',
    'bookstore',
    'bt_league',
    'bt_cup',
    'cup',
    'features',
    'escala_de_plantao',
    'payments',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

X_FRAME_OPTIONS = 'SAMEORIGIN'

ROOT_URLCONF = 'setup.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'setup.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
AUTHENTICATION_BACKENDS = ['setup.config.auth.UsernameOrEmailBackend']

# Internationalization
LANGUAGE_CODE = 'pt-br'
USE_I18N = True
USE_TZ = True
TIME_ZONE = 'America/Sao_Paulo'

# apps folder
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

# Static files (CSS, JavaScript, Images)
STATICFILES_DIRS = [ BASE_DIR / 'setup/static' ]
STATIC_ROOT = BASE_DIR / 'static'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
if DEBUG:
    STATIC_URL = '/static/'
else:
    STATIC_URL = os.getenv('APP_LINK') + '/admin_assets/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# locale
LOCALE_PATHS = [ BASE_DIR / 'locale' ]

# CORS
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'content-type',
    'x-csrftoken',
    'authorization',
]
CORS_ALLOWED_ORIGINS = json.loads(os.getenv('CORS_ALLOWED_ORIGINS', '[]'))
CORS_EXPOSE_HEADERS = ['x-csrftoken']

# CSRF
CSRF_TRUSTED_ORIGINS = json.loads(os.getenv('CORS_ALLOWED_ORIGINS', '[]'))
CSRF_COOKIE_NAME = 'podio-digital-csrftoken'
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 86400
if DEBUG:
    CSRF_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False
else:
    CSRF_COOKIE_HTTPONLY = False
    CSRF_COOKIE_PARTITIONED = True
    CSRF_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SECURE = True

    SESSION_COOKIE_PARTITIONED = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True

# EMAIL
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

# Jazzmin
from .theme import JAZZMIN_UI_TWEAKS, JAZZMIN_SETTINGS
