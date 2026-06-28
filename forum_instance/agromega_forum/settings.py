import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("FORUM_SECRET_KEY", os.getenv("SECRET_KEY", "unsafe-local-forum-secret-key"))
DEBUG = os.getenv("FORUM_DEBUG", "False").lower() == "true"

FORUM_SITE_URL = os.getenv("FORUM_SITE_URL", "http://localhost:8001").rstrip("/")
MAIN_SITE_URL = os.getenv("MAIN_SITE_URL", "http://localhost:8000").rstrip("/")
ALLOWED_HOSTS = os.getenv("FORUM_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
CSRF_TRUSTED_ORIGINS = os.getenv("FORUM_CSRF_TRUSTED_ORIGINS", FORUM_SITE_URL).split(",")
FORCE_SCRIPT_NAME = os.getenv("FORUM_FORCE_SCRIPT_NAME") or None
USE_X_FORWARDED_HOST = os.getenv("FORUM_USE_X_FORWARDED_HOST", "True").lower() == "true"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "social_django",
    "forum_sso",
    "spirit.core",
    "spirit.admin",
    "spirit.search",
    "spirit.user",
    "spirit.user.admin",
    "spirit.user.auth",
    "spirit.category",
    "spirit.category.admin",
    "spirit.topic",
    "spirit.topic.admin",
    "spirit.topic.favorite",
    "spirit.topic.moderate",
    "spirit.topic.notification",
    "spirit.topic.private",
    "spirit.topic.unread",
    "spirit.comment",
    "spirit.comment.bookmark",
    "spirit.comment.flag",
    "spirit.comment.flag.admin",
    "spirit.comment.history",
    "spirit.comment.like",
    "spirit.comment.poll",
    "djconfig",
    "haystack",
]

if os.getenv("FORUM_STORAGE_BACKEND", "").lower() == "s3":
    INSTALLED_APPS.append("storages")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "spirit.user.middleware.TimezoneMiddleware",
    "spirit.user.middleware.LastIPMiddleware",
    "spirit.user.middleware.LastSeenMiddleware",
    "spirit.user.middleware.ActiveUserMiddleware",
    "spirit.core.middleware.PrivateForumMiddleware",
    "djconfig.middleware.DjConfigMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
                "djconfig.context_processors.config",
                "forum_sso.context_processors.site_links",
            ]
        },
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("FORUM_POSTGRES_DB"),
        "USER": os.getenv("FORUM_POSTGRES_USER"),
        "PASSWORD": os.getenv("FORUM_POSTGRES_PASSWORD"),
        "HOST": os.getenv("FORUM_POSTGRES_HOST"),
        "PORT": os.getenv("FORUM_POSTGRES_PORT"),
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "spirit_cache",
    },
    "st_rate_limit": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "spirit_rl_cache",
        "TIMEOUT": None,
    },
}

AUTHENTICATION_BACKENDS = [
    "social_core.backends.open_id_connect.OpenIdConnectAuth",
    "django.contrib.auth.backends.ModelBackend",
    "spirit.user.auth.backends.UsernameAuthBackend",
    "spirit.user.auth.backends.EmailAuthBackend",
]

ROOT_URLCONF = "agromega_forum.urls"
WSGI_APPLICATION = "agromega_forum.wsgi.application"
ASGI_APPLICATION = "agromega_forum.asgi.application"

LOGIN_URL = "sso-start"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = f"{MAIN_SITE_URL}/logout/?local=1"

SOCIAL_AUTH_URL_NAMESPACE = "social"
SOCIAL_AUTH_LOGIN_REDIRECT_URL = "/"
SOCIAL_AUTH_LOGIN_ERROR_URL = "/sso/error/"
SOCIAL_AUTH_RAISE_EXCEPTIONS = False
SOCIAL_AUTH_USER_FIELDS = ["username", "email", "first_name", "last_name"]
SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = os.getenv("FORUM_OIDC_ENDPOINT", f"{MAIN_SITE_URL}/o")
SOCIAL_AUTH_OIDC_KEY = os.getenv("FORUM_OIDC_CLIENT_ID", "agromega-forum")
SOCIAL_AUTH_OIDC_SECRET = os.getenv("FORUM_OIDC_CLIENT_SECRET", "")
SOCIAL_AUTH_OIDC_ACCESS_TOKEN_URL = os.getenv(
    "FORUM_OIDC_TOKEN_URL",
    f"{SOCIAL_AUTH_OIDC_OIDC_ENDPOINT}/token/",
)
SOCIAL_AUTH_OIDC_USERINFO_URL = os.getenv(
    "FORUM_OIDC_USERINFO_URL",
    f"{SOCIAL_AUTH_OIDC_OIDC_ENDPOINT}/userinfo/",
)
SOCIAL_AUTH_OIDC_JWKS_URI = os.getenv(
    "FORUM_OIDC_JWKS_URI",
    f"{SOCIAL_AUTH_OIDC_OIDC_ENDPOINT}/.well-known/jwks.json",
)
SOCIAL_AUTH_OIDC_SCOPE = ["openid", "profile", "email"]
SOCIAL_AUTH_OIDC_USERNAME_KEY = "preferred_username"
SOCIAL_AUTH_REDIRECT_IS_HTTPS = (
    os.getenv(
        "FORUM_SOCIAL_AUTH_REDIRECT_IS_HTTPS",
        "True" if FORUM_SITE_URL.startswith("https://") else "False",
    ).lower()
    == "true"
)
SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "forum_sso.pipeline.create_or_update_forum_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.whoosh_backend.WhooshEngine",
        "PATH": str(BASE_DIR / "st_search"),
    }
}
HAYSTACK_SIGNAL_PROCESSOR = "spirit.search.signals.RealtimeSignalProcessor"

LANGUAGE_CODE = os.getenv("FORUM_LANGUAGE_CODE", "uk")
LANGUAGES = [("uk", "Ukrainian")]
TIME_ZONE = os.getenv("FORUM_TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
LOCALE_PATHS = [BASE_DIR / "locale"]

STATIC_URL = os.getenv("FORUM_STATIC_URL", "/forum/static/" if FORCE_SCRIPT_NAME else "/static/")
STATIC_ROOT = os.getenv("FORUM_STATIC_ROOT", "/static")
MEDIA_URL = os.getenv("FORUM_MEDIA_URL", "/forum/media/" if FORCE_SCRIPT_NAME else "/media/")
MEDIA_ROOT = os.getenv("FORUM_MEDIA_ROOT", str(BASE_DIR / "media"))
STORAGES = {
    "default": {"BACKEND": "spirit.core.storage.OverwriteFileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

if os.getenv("FORUM_STORAGE_BACKEND", "").lower() == "s3":
    FORUM_AWS_ACCESS_KEY_ID = os.getenv("FORUM_AWS_ACCESS_KEY_ID", "")
    FORUM_AWS_SECRET_ACCESS_KEY = os.getenv("FORUM_AWS_SECRET_ACCESS_KEY", "")
    FORUM_AWS_STORAGE_BUCKET_NAME = os.getenv("FORUM_AWS_STORAGE_BUCKET_NAME", "")
    FORUM_AWS_S3_ENDPOINT_URL = os.getenv("FORUM_AWS_S3_ENDPOINT_URL", "").strip()
    FORUM_AWS_S3_CUSTOM_DOMAIN = os.getenv("FORUM_AWS_S3_CUSTOM_DOMAIN", "").strip()
    FORUM_AWS_S3_REGION_NAME = os.getenv("FORUM_AWS_S3_REGION_NAME", "")
    FORUM_AWS_MEDIA_LOCATION = os.getenv("FORUM_AWS_MEDIA_LOCATION", "media").strip("/")

    if FORUM_AWS_S3_ENDPOINT_URL and not FORUM_AWS_S3_ENDPOINT_URL.startswith(("http://", "https://")):
        FORUM_AWS_S3_ENDPOINT_URL = f"https://{FORUM_AWS_S3_ENDPOINT_URL}"

    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "access_key": FORUM_AWS_ACCESS_KEY_ID,
            "secret_key": FORUM_AWS_SECRET_ACCESS_KEY,
            "bucket_name": FORUM_AWS_STORAGE_BUCKET_NAME,
            "endpoint_url": FORUM_AWS_S3_ENDPOINT_URL or None,
            "region_name": FORUM_AWS_S3_REGION_NAME or None,
            "custom_domain": FORUM_AWS_S3_CUSTOM_DOMAIN or None,
            "querystring_auth": False,
            "default_acl": "public-read",
            "file_overwrite": False,
            "object_parameters": {"CacheControl": "max-age=86400"},
            "location": FORUM_AWS_MEDIA_LOCATION,
        },
    }

    if not os.getenv("FORUM_MEDIA_URL"):
        if FORUM_AWS_S3_CUSTOM_DOMAIN:
            MEDIA_URL = f"https://{FORUM_AWS_S3_CUSTOM_DOMAIN}/{FORUM_AWS_MEDIA_LOCATION}/"
        elif FORUM_AWS_STORAGE_BUCKET_NAME and FORUM_AWS_S3_ENDPOINT_URL:
            endpoint_host = FORUM_AWS_S3_ENDPOINT_URL.removeprefix("https://").removeprefix("http://")
            MEDIA_URL = f"https://{FORUM_AWS_STORAGE_BUCKET_NAME}.{endpoint_host}/{FORUM_AWS_MEDIA_LOCATION}/"

ST_SITE_URL = FORUM_SITE_URL
ST_UPLOAD_FILE_ENABLED = False
ST_UPLOAD_IMAGE_ENABLED = True
ST_NOTIFY_WHEN = "never"
ST_NGRAM_SEARCH = True

# Basic logging to console for local development (prints tracebacks)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG" if os.getenv("FORUM_DEBUG", "False").lower() == "true" else "INFO",
    },
}

# Session / cookie settings tuned for local development behind nginx proxy.
# Ensure the forum session cookie is available on the root path and sent when
# the provider redirects the user back to the forum during the OIDC flow.
SESSION_COOKIE_DOMAIN = os.getenv("FORUM_COOKIE_DOMAIN", "localhost")
SESSION_COOKIE_PATH = "/"
# Lax allows cookies to be sent on top-level GET navigations (sufficient for OIDC redirects)
SESSION_COOKIE_SAMESITE = os.getenv("FORUM_COOKIE_SAMESITE", "Lax")
SESSION_COOKIE_SECURE = os.getenv("FORUM_COOKIE_SECURE", "False").lower() == "true"

# Use distinct cookie names so the forum and main site sessions do not overwrite each other
# when both run on the same domain (helps OIDC flows where the user is redirected
# between main and forum and each site sets its own session cookie).
SESSION_COOKIE_NAME = os.getenv("FORUM_SESSION_COOKIE_NAME", "forum_sessionid")
CSRF_COOKIE_NAME = os.getenv("FORUM_CSRF_COOKIE_NAME", "forum_csrftoken")

# CSRF cookie to match session cookie behavior (helpful during development)
CSRF_COOKIE_DOMAIN = SESSION_COOKIE_DOMAIN
CSRF_COOKIE_PATH = SESSION_COOKIE_PATH
CSRF_COOKIE_SAMESITE = SESSION_COOKIE_SAMESITE
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
