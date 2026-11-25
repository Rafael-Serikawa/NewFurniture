"""
Configurações do projeto NewFurniture (PMR3304 - Sistemas de Informação).

Backend: Django + Django REST Framework + SQLite.
Autenticação da API: Token (rest_framework.authtoken).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Em produção (Render) defina DJANGO_SECRET_KEY e DJANGO_DEBUG=0 nas variáveis de ambiente.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-newfurniture-pmr3304-2026-troque-em-producao')
DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'
ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com']
# O Render termina o HTTPS no proxy: assim o Django gera links https (imagens, admin).
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'core',
]

MIDDLEWARE = [
    'core.middleware.CorsMiddleware',  # permite o frontend (outra porta) consumir a API
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# WhiteNoise serve os arquivos estáticos (admin, API navegável) em produção.
try:
    import whitenoise  # noqa: F401
    MIDDLEWARE.insert(2, 'whitenoise.middleware.WhiteNoiseMiddleware')
except ImportError:
    pass

ROOT_URLCONF = 'newfurniture.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'newfurniture.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Usuário customizado: superentidade "Usuario" do DER (Cliente, Designer e
# Marceneiro são especializações dela).
AUTH_USER_MODEL = 'core.Usuario'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 6}},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Build do React (npm run build) — se existir, o Django também serve o frontend.
FRONTEND_DIST = BASE_DIR.parent / 'frontend' / 'dist'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # valores decimais saem como número no JSON (e não como string)
    'COERCE_DECIMAL_TO_STRING': False,
}
