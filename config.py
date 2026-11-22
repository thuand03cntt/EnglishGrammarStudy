import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-english-practice-secret-key-change-in-prod-2026")
    
    # Database configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_USER = os.getenv("DB_USER", "practice_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "practice_password123")
    DB_NAME = os.getenv("DB_NAME", "english_practice_db")
    
    # Priority: explicit DATABASE_URL > constructed MariaDB URL > fallback SQLite
    CUSTOM_DB_URI = os.getenv("DATABASE_URL")
    if CUSTOM_DB_URI:
        SQLALCHEMY_DATABASE_URI = CUSTOM_DB_URI
    elif os.getenv("USE_SQLITE", "false").lower() in ("true", "1", "yes"):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'database' / 'english_practice.db'}"
    else:
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
        )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
        "pool_size": 20,
        "max_overflow": 40,
    }
    
    # File upload configurations
    UPLOAD_FOLDER = BASE_DIR / "static" / "uploads" / "avatars"
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max upload
    
    # Flask-Mail configuration
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() in ("true", "1", "yes")
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "false").lower() in ("true", "1", "yes")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@englishpractice.local")
    # If MAIL_SUPPRESS_SEND is True or credentials empty, mail service logs to console
    MAIL_SUPPRESS_SEND = os.getenv("MAIL_SUPPRESS_SEND", "false").lower() in ("true", "1", "yes") or not os.getenv("MAIL_USERNAME")

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'database' / 'test.db'}"
    MAIL_SUPPRESS_SEND = True
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
