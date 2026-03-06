import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class DevelopmentConfig:
    DEBUG = True
    SECRET_KEY = os.environ.get("SECRET_KEY", "univdz-secret-key-2024")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "..", "univdz.db")

    # évite les connexions mortes à la base
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True
    }


class ProductionConfig:
    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY", "univdz-secret-key-2024")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DATABASE_URL = os.environ.get("DATABASE_URL", "")

    # correction format Render
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    # stabilise la connexion PostgreSQL
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True
    }


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}