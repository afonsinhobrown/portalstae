import os
from pathlib import Path
from django.contrib.messages import constants as messages

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-sua-chave-secreta-aqui-mude-em-producao'
DEBUG = False
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.localhost', '0.0.0.0', '.onrender.com', '*']

INSTALLED_APPS = [
    'daphne',  # REQUIRED for ASGI/Channels (must be at top)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    'admin_portal',
    'recursoshumanos',
   'gestaoequipamentos',
   'gestaocombustivel',
   'credenciais',
   'pagina_stae',
    'chatbot',
    'dfec',
    'channels',  # REQUIRED for WebSockets
    
    # Novas Apps - Sistema Eleitoral Completo
    'ugea',  # Gestão de Concursos Públicos
    'partidos',  # Gestão de Partidos Políticos
    'circuloseleitorais',  # Gestão de Círculos Eleitorais
    'eleicao',  # Gestão de Eleições (NOVA APP)
    'candidaturas',  # Gestão de Candidaturas
    'rs',  # Recenseamento & Logística
    'apuramento',  # Apuramento de Resultados

    #'ckeditor',
    #'markdownify',
]

# ========== MIDDLEWARE SEM CSRF ==========
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # NÃO TEM CSRF MIDDLEWARE AQUI - REMOVIDO
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'portalstae.urls'

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

WSGI_APPLICATION = 'portalstae.wsgi.application'
ASGI_APPLICATION = 'portalstae.asgi.application'  # REQUIRED for Channels

# Channels Layer (Development)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'portalstae',
        'USER': 'neondb_owner',
        'PASSWORD': 'npg_xP2dwTc1kLqn',
        'HOST': 'ep-long-king-agnipa9p-pooler.c-2.eu-central-1.aws.neon.tech',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',
            'client_encoding': 'UTF8',
        }
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'pt-pt'
TIME_ZONE = 'Africa/Maputo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# ========== CSRF DESATIVADO ==========
APP_LOGIN_URLS = {
    'dfec': '/dfec/login/',
    'recursoshumanos': '/recursoshumanos/login/',
}

CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000', 'https://*.onrender.com', 'https://portalstae.onrender.com']
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False

# Aumentar limite de upload para imagens de propostas e manuais grandes
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB

# Configurações específicas
STAEL_CONFIG = {
    'API_TOKEN': 'seu-token-seguro-aqui',
    'UPDATE_INTERVAL': 30,
    'MAX_RESULTS': 1000000,
}

CHATBOT_CONFIG = {
    'MAX_CONVERSATION_HISTORY': 10,
    'SIMILARITY_THRESHOLD': 0.3,
    'ENABLE_EXTERNAL_SOURCES': True,
    'FALLBACK_ENABLED': True,
    'SEMANTIC_SEARCH_ENABLED': True,
    'LEARNING_SYSTEM_ENABLED': True,
}

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 600 # 10 minutos (ajustado de 3m para evitar logouts durante escrita)
SESSION_SAVE_EVERY_REQUEST = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

MARKDOWNIFY = {
    "default": {
        "WHITELIST_TAGS": [
            'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em',
            'i', 'li', 'ol', 'p', 'strong', 'ul', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
        ],
        "MARKDOWN_EXTENSIONS": [
            'markdown.extensions.fenced_code',
            'markdown.extensions.tables',
        ]
    }
}
