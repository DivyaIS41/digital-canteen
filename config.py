import os
from dotenv import load_dotenv

load_dotenv()


def env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def is_production():
    return os.getenv("FLASK_ENV", "").strip().lower() == "production"


def build_mysql_config():
    return {
        "host": os.getenv("DB_HOST", "").strip(),
        "port": env_int("DB_PORT", 3306),
        "user": os.getenv("DB_USER", "").strip(),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "").strip(),
        "ssl_mode": os.getenv("DB_SSL_MODE", "").strip(),
        "ssl_ca": os.getenv("DB_SSL_CA", "").strip(),
    }


def validate_env(required_keys):
    missing = [key for key in required_keys if not os.getenv(key)]
    return missing


def validate_secret_key(secret_key):
    weak_values = {
        "",
        "your_super_secret_key_here",
        "dev_secret_key",
        "changeme",
    }
    if secret_key in weak_values:
        return False
    return len(secret_key) >= 32


def apply_flask_config(app):
    secret_key = os.getenv("FLASK_SECRET_KEY", "")
    if not validate_secret_key(secret_key):
        raise RuntimeError(
            "FLASK_SECRET_KEY is missing or too weak. Use a long random secret."
        )

    app.secret_key = secret_key
    app.config["ENV"] = os.getenv("FLASK_ENV", "development")
    app.config["DEBUG"] = env_flag("FLASK_DEBUG", default=not is_production())
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = env_flag(
        "SESSION_COOKIE_SECURE", default=is_production()
    )
    app.config["PREFERRED_URL_SCHEME"] = "https" if is_production() else "http"
    app.config["PERMANENT_SESSION_LIFETIME"] = env_int(
        "SESSION_LIFETIME_SECONDS", 7200
    )
