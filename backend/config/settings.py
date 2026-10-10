from pathlib import Path
from datetime import timedelta
from decouple import config

# ============================================================
# BASE PATHS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent  # internet-banking/ folder


# ============================================================
# SECURITY
# ============================================================
SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-CHANGE-ME-IN-PRODUCTION-xyz123-abc456'
)
DEBUG = config('DEBUG', cast=bool, default=True)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,0.0.0.0'
).split(',')


# ============================================================
# APPLICATIONS
# ============================================================
INSTALLED_APPS = [
    # Django default
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'drf_spectacular',

    # Celery
    'django_celery_beat',
    'django_celery_results',

    # Local apps — Authentication & Core
    'apps.users',
    'apps.accounts',
    'apps.transactions',
    'apps.beneficiaries',
    'apps.kyc',

    # Local apps — Banking Features
    'apps.bills',
    'apps.cards',
    'apps.loans',

    # Local apps — Support
    'apps.notifications',
    'apps.complaints',

    # Local apps — Infrastructure
    'apps.audit',
    'apps.otp_service',

    # ML Pipeline
    'apps.ml_pipeline',
    'apps.chat'
]


# ============================================================
# MIDDLEWARE
# ============================================================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Custom
    'apps.audit.middleware.AuditMiddleware',
]

ROOT_URLCONF = 'config.urls'


# ============================================================
# TEMPLATES
# ============================================================
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

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'


# ============================================================
# DATABASE — PostgreSQL
# ============================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='internet_banking'),
        'USER': config('DB_USER', default='bank_admin'),
        'PASSWORD': config('DB_PASSWORD', default='BankAdmin@2024'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}


# ============================================================
# CUSTOM USER MODEL
# ============================================================
AUTH_USER_MODEL = 'users.User'


# ============================================================
# PASSWORD VALIDATION
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Dhaka'
USE_I18N = True
USE_TZ = True


# ============================================================
# STATIC & MEDIA FILES
# ============================================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================================
# REST FRAMEWORK
# ============================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '5/min',
        'otp_request': '3/min',
        'transfer': '20/hour',
    },
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATE_FORMAT': '%Y-%m-%d',
}


# ============================================================
# JWT — Simple JWT
# ============================================================
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=config('JWT_ACCESS_MINUTES', cast=int, default=30)
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=config('JWT_REFRESH_DAYS', cast=int, default=7)
    ),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'user_id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE':
        'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=30),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
}


# ============================================================
# CORS — Frontend Access
# ============================================================
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173'
).split(',')

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:3000,http://localhost:8000'
).split(',')


# ============================================================
# DRF SPECTACULAR — API Documentation
# ============================================================
SPECTACULAR_SETTINGS = {
    'TITLE': 'Internet Banking System API',
    'DESCRIPTION': (
        'Full-featured Internet Banking REST API with AI-powered fraud detection, '
        'KYC, transactions, loans, cards, bills, and notifications.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'filter': True,
    },
    'SECURITY': [
        {'jwtAuth': []},
    ],
    'COMPONENTS': {
        'securitySchemes': {
            'jwtAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
        }
    },
}


# ============================================================
# CELERY — Distributed Task Queue
# ============================================================
CELERY_BROKER_URL = config(
    'CELERY_BROKER_URL',
    default='redis://localhost:6379/0'
)
CELERY_RESULT_BACKEND = config(
    'CELERY_RESULT_BACKEND',
    default='redis://localhost:6379/1'
)

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Dhaka'
CELERY_ENABLE_UTC = True

CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 60 * 60           # 1 hour hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 55 * 60      # 55 min soft limit
CELERY_RESULT_EXPIRES = 60 * 60 * 24 * 7   # 7 days
CELERY_TASK_ALWAYS_EAGER = False           # True for testing without worker
CELERY_TASK_EAGER_PROPAGATES = True

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_SYNC_EVERY = 1

CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100
CELERY_WORKER_HIJACK_ROOT_LOGGER = False

# Task routes
CELERY_TASK_ROUTES = {
    'apps.ml_pipeline.tasks.*': {'queue': 'ml'},
    'apps.notifications.tasks.*': {'queue': 'notifications'},
    'apps.otp_service.tasks.*': {'queue': 'fast'},
}


# ============================================================
# AI MICROSERVICE
# ============================================================
AI_SERVICE_URL = config('AI_SERVICE_URL', default='http://localhost:9000')
AI_SERVICE_TIMEOUT = config('AI_SERVICE_TIMEOUT', cast=int, default=5)

AI_ENDPOINTS = {
    'FRAUD_PREDICT': f'{AI_SERVICE_URL}/fraud/predict',
    'FRAUD_EXPLAIN': f'{AI_SERVICE_URL}/fraud/explain',
    'FRAUD_MODEL_INFO': f'{AI_SERVICE_URL}/fraud/model-info',
    'CHATBOT_ASK': f'{AI_SERVICE_URL}/chatbot/ask',
    'CREDIT_SCORE': f'{AI_SERVICE_URL}/credit/score',
    'HEALTH': f'{AI_SERVICE_URL}/health',
}


# ============================================================
# ML PIPELINE CONFIGURATION
# ============================================================
ML_PIPELINE = {
    'AI_SERVICE_DIR': config('AI_SERVICE_DIR', default=str(PROJECT_ROOT / 'ai-service')),
    'MIN_AUPRC_IMPROVEMENT': 0.005,      # New model must beat old by 0.5%
    'MIN_RECALL': 0.75,                   # Hard floor for recall
    'MIN_PRECISION': 0.75,                # Hard floor for precision
    'AUTO_ACTIVATE': True,                # Auto-switch to better model
    'KEEP_LAST_VERSIONS': 10,             # Cleanup threshold
    'DRIFT_PSI_THRESHOLD': 0.25,          # Significant drift
    'DRIFT_AUTO_RETRAIN_THRESHOLD': 0.5,  # Severe drift triggers retrain
    'RETRAIN_SCHEDULE_HOURS': 24 * 7,     # Weekly
}


# ============================================================
# BANKING BUSINESS RULES
# ============================================================
BANKING = {
    'DAILY_TRANSFER_LIMIT': 500000,       # ৳5,00,000
    'PER_TRANSACTION_LIMIT': 200000,      # ৳2,00,000
    'MIN_TRANSFER_AMOUNT': 1,             # ৳1
    'OTP_EXPIRY_MINUTES': 5,
    'MAX_OTP_ATTEMPTS': 3,
    'OTP_LOCKOUT_MINUTES': 30,
    'FRAUD_HOLD_THRESHOLD': 0.8,          # Hold txn if score > 0.8
    'FRAUD_ALERT_THRESHOLD': 0.5,         # Notify admin if score > 0.5
    'ACCOUNT_NUMBER_PREFIX': '10',
    'DEFAULT_CURRENCY': 'BDT',
    'KYC_AUTO_APPROVE': False,
    'SESSION_INACTIVITY_MINUTES': 30,
}


# ============================================================
# EMAIL CONFIGURATION
# ============================================================
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', cast=int, default=587)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool, default=True)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@ibs.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL


# ============================================================
# SMS CONFIGURATION (SSL Wireless / Twilio)
# ============================================================
SMS_PROVIDER = config('SMS_PROVIDER', default='console')  # 'sslwireless', 'twilio', 'console'

SSL_WIRELESS = {
    'API_URL': config('SSL_SMS_API_URL', default='https://smsplus.sslwireless.com/api/v3/send-sms'),
    'API_TOKEN': config('SSL_SMS_API_TOKEN', default=''),
    'SID': config('SSL_SMS_SID', default=''),
    'SENDER_ID': config('SSL_SMS_SENDER_ID', default='IBS'),
}

TWILIO = {
    'ACCOUNT_SID': config('TWILIO_ACCOUNT_SID', default=''),
    'AUTH_TOKEN': config('TWILIO_AUTH_TOKEN', default=''),
    'FROM_NUMBER': config('TWILIO_FROM_NUMBER', default=''),
}


# ============================================================
# CACHE — Redis
# ============================================================
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://localhost:6379/2'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,
        },
        'KEY_PREFIX': 'ibs',
        'TIMEOUT': 300,
    }
}

# Fallback to local memory if django_redis not installed
try:
    import django_redis  # noqa
except ImportError:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'ibs-cache',
        }
    }


# ============================================================
# LOGGING
# ============================================================
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django.log',
            'maxBytes': 10 * 1024 * 1024,   # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'errors.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'ERROR',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


# ============================================================
# FILE UPLOAD SETTINGS
# ============================================================
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024      # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

KYC_UPLOAD_MAX_SIZE = 5 * 1024 * 1024               # 5 MB per file
ALLOWED_KYC_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.pdf']
ALLOWED_KYC_MIME_TYPES = [
    'image/jpeg', 'image/png', 'image/jpg', 'application/pdf'
]


# ============================================================
# SECURITY HEADERS (Production)
# ============================================================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000                # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# ============================================================
# SESSION SETTINGS
# ============================================================
SESSION_COOKIE_AGE = 60 * 60 * 24        # 24 hours
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_COOKIE_HTTPONLY = False             # React needs to read it
CSRF_COOKIE_SAMESITE = 'Lax'


# ============================================================
# AZURE BLOB STORAGE (Production)
# ============================================================
AZURE_STORAGE_ENABLED = config('AZURE_STORAGE_ENABLED', cast=bool, default=False)

if AZURE_STORAGE_ENABLED:
    DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'
    AZURE_ACCOUNT_NAME = config('AZURE_ACCOUNT_NAME', default='')
    AZURE_ACCOUNT_KEY = config('AZURE_ACCOUNT_KEY', default='')
    AZURE_CONTAINER = config('AZURE_CONTAINER', default='media')
    AZURE_SSL = True
    AZURE_LOCATION = 'media'


# ============================================================
# AZURE APPLICATION INSIGHTS (Optional)
# ============================================================
APPINSIGHTS_INSTRUMENTATIONKEY = config(
    'APPINSIGHTS_INSTRUMENTATIONKEY', default=''
)
APPLICATIONINSIGHTS_CONNECTION_STRING = config(
    'APPLICATIONINSIGHTS_CONNECTION_STRING', default=''
)

if APPINSIGHTS_INSTRUMENTATIONKEY:
    MIDDLEWARE.insert(0, 'django.middleware.common.BrokenLinkEmailsMiddleware')


# ============================================================
# SENTRY (Error Tracking — Optional)
# ============================================================
SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN and not DEBUG:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration(), CeleryIntegration()],
            traces_sample_rate=0.1,
            send_default_pii=False,
            environment='production' if not DEBUG else 'development',
        )
    except ImportError:
        pass


# ============================================================
# ADMIN
# ============================================================
ADMIN_URL = config('ADMIN_URL', default='admin/')
ADMIN_SITE_HEADER = 'Internet Banking System Admin'
ADMIN_SITE_TITLE = 'IBS Admin'
ADMIN_INDEX_TITLE = 'Dashboard'


# ============================================================
# THIRD-PARTY API KEYS
# ============================================================
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')
PORICHOY_API_KEY = config('PORICHOY_API_KEY', default='')      # NID verification
SSLCOMMERZ_STORE_ID = config('SSLCOMMERZ_STORE_ID', default='')
SSLCOMMERZ_STORE_PASSWORD = config('SSLCOMMERZ_STORE_PASSWORD', default='')


# ============================================================
# FEATURE FLAGS
# ============================================================
FEATURES = {
    'ENABLE_AI_FRAUD': config('ENABLE_AI_FRAUD', cast=bool, default=True),
    'ENABLE_CHATBOT': config('ENABLE_CHATBOT', cast=bool, default=True),
    'ENABLE_NID_OCR': config('ENABLE_NID_OCR', cast=bool, default=False),
    'ENABLE_LOAN_AI_SCORING': config('ENABLE_LOAN_AI_SCORING', cast=bool, default=True),
    'ENABLE_EMAIL_NOTIFICATIONS': config('ENABLE_EMAIL_NOTIFICATIONS', cast=bool, default=True),
    'ENABLE_SMS_NOTIFICATIONS': config('ENABLE_SMS_NOTIFICATIONS', cast=bool, default=False),
    'ENABLE_2FA_REQUIRED': config('ENABLE_2FA_REQUIRED', cast=bool, default=True),
    'MAINTENANCE_MODE': config('MAINTENANCE_MODE', cast=bool, default=False),
}


# ============================================================
# CONSTANTS
# ============================================================
IBAN_PREFIX = 'BD'
ACCOUNT_NUMBER_LENGTH = 12
TRANSACTION_REF_PREFIX = 'TXN'
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100