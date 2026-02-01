from pathlib import Path

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'example_secret_key_change_in_production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

ALLOWED_HOSTS = ['*']

# Keycloak OIDC (для локальной разработки задайте свои значения)
KEYCLOAK_SERVER_URL = 'https://keycloak.example.com'
KEYCLOAK_REALM = 'ptp'
OIDC_RP_CLIENT_ID = 'ptp'
OIDC_RP_CLIENT_SECRET = 'client-secret'
OIDC_OP_AUTHORIZATION_ENDPOINT = f'{KEYCLOAK_SERVER_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/auth'
OIDC_OP_TOKEN_ENDPOINT = f'{KEYCLOAK_SERVER_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token'
OIDC_OP_USER_ENDPOINT = f'{KEYCLOAK_SERVER_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/userinfo'
OIDC_OP_JWKS_ENDPOINT = f'{KEYCLOAK_SERVER_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs'
OIDC_OP_LOGOUT_ENDPOINT = f'{KEYCLOAK_SERVER_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/logout'

SITE_URL = 'https://localhost'
OIDC_RP_REDIRECT_URI = f'{SITE_URL}/oidc/callback/'
CSRF_TRUSTED_ORIGINS = ['http://localhost', 'https://localhost', 'http://127.0.0.1:8000']
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Celery Configuration
CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
