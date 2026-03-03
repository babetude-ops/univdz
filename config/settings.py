import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class DevelopmentConfig:
    DEBUG = True
    SECRET_KEY = "univdz-secret-key-2024"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "..", "univdz.db")


class ProductionConfig:
    DEBUG = False
    SECRET_KEY = "univdz-secret-key-2024"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "..", "univdz.db")


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}