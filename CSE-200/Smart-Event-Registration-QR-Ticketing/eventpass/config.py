"""Application configuration for local development and Vercel production."""

import os


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _normalize_database_url(raw_url: str) -> str:
    """Use psycopg 3 explicitly for PostgreSQL URLs supplied by Neon/Vercel."""
    value = (raw_url or "").strip()
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    return value


IS_VERCEL = _as_bool(os.getenv("VERCEL"), False)
_RAW_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///eventpass.db")
_DATABASE_URL = _normalize_database_url(_RAW_DATABASE_URL)

if IS_VERCEL and not _DATABASE_URL.startswith("postgresql+psycopg://"):
    raise RuntimeError(
        "EventPass on Vercel requires a persistent PostgreSQL DATABASE_URL. "
        "Connect Neon or another PostgreSQL provider in Vercel and set DATABASE_URL."
    )
if IS_VERCEL and (not os.getenv("SECRET_KEY") or len(os.getenv("SECRET_KEY", "")) < 32):
    raise RuntimeError("Set SECRET_KEY to a random value of at least 32 characters in Vercel Environment Variables.")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "local-development-only-change-this-secret")

    SQLALCHEMY_DATABASE_URI = _DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    if _DATABASE_URL.startswith("postgresql+psycopg://"):
        # Neon pooled URLs are recommended for serverless deployments.
        SQLALCHEMY_ENGINE_OPTIONS.update(
            {
                "pool_size": int(os.getenv("DB_POOL_SIZE", "1")),
                "max_overflow": 0,
                "pool_recycle": 300,
                "pool_timeout": 15,
            }
        )

    WTF_CSRF_TIME_LIMIT = 3600
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    APP_NAME = os.getenv("APP_NAME", "EventPass")
    _vercel_host = os.getenv("VERCEL_PROJECT_PRODUCTION_URL") or os.getenv("VERCEL_URL", "")
    APP_BASE_URL = os.getenv(
        "APP_BASE_URL",
        f"https://{_vercel_host}" if IS_VERCEL and _vercel_host else "http://127.0.0.1:5000",
    ).rstrip("/")
    TIMEZONE = os.getenv("TIMEZONE", "Asia/Dhaka")

    # Local development creates tables automatically. On Vercel, initialize the
    # PostgreSQL schema once with `python manage.py init-db` and keep this false.
    AUTO_CREATE_DB = _as_bool(os.getenv("AUTO_CREATE_DB"), default=not IS_VERCEL)
    IS_VERCEL = IS_VERCEL

    MAIL_SERVER = os.getenv("MAIL_SERVER", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = _as_bool(os.getenv("MAIL_USE_TLS"), True)
    MAIL_USE_SSL = _as_bool(os.getenv("MAIL_USE_SSL"), False)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "")
    MAIL_TIMEOUT = int(os.getenv("MAIL_TIMEOUT", "15"))
    MAIL_SUPPRESS_SEND = _as_bool(os.getenv("MAIL_SUPPRESS_SEND"), False)

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _as_bool(os.getenv("SESSION_COOKIE_SECURE"), IS_VERCEL)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = _as_bool(os.getenv("SESSION_COOKIE_SECURE"), IS_VERCEL)
