"""
Settings de PRODUCTION pour CESIZen.
Hérite de settings.py et surcharge les valeurs sensibles.
Variable : DJANGO_SETTINGS_MODULE=CEZIZen.settings_prod
"""

from .settings import *  # noqa
import os

# ── Sécurité ──────────────────────────────────────────────────────────────────
DEBUG = False
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]  # Obligatoire — plante si absent
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost").split(",")

# ── HTTPS ─────────────────────────────────────────────────────────────────────
# Off by default until a reverse proxy + real TLS certs sit in front of this
# app again — with no proxy, forcing a redirect to https:// just hangs the
# request since nothing is listening on 443. Set DJANGO_SECURE_SSL_REDIRECT=True
# once that's back in place.
_HTTPS_ENABLED = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "False") == "True"
SECURE_SSL_REDIRECT = _HTTPS_ENABLED
SESSION_COOKIE_SECURE = _HTTPS_ENABLED
CSRF_COOKIE_SECURE = _HTTPS_ENABLED
SECURE_HSTS_SECONDS = 31536000 if _HTTPS_ENABLED else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = _HTTPS_ENABLED
SECURE_HSTS_PRELOAD = _HTTPS_ENABLED
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ── Base de données MariaDB ────────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.mysql"),
        "NAME": os.environ.get("DB_NAME", "cesizen_prod"),
        "USER": os.environ.get("DB_USER", "cesizen_user"),
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.environ.get("DB_HOST", "db"),
        "PORT": os.environ.get("DB_PORT", "3306"),
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

# ── Email SMTP ────────────────────────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.mailgun.org")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("DJANGO_DEFAULT_FROM_EMAIL", "noreply@cesizen.fr")
