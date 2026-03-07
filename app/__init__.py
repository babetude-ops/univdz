from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from apscheduler.schedulers.background import BackgroundScheduler

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
scheduler = BackgroundScheduler()


def create_app(config_name="default"):
    app = Flask(__name__)

    # Charger la configuration
    from config.settings import config
    app.config.from_object(config[config_name])

    # ─── Options SQLAlchemy seulement pour PostgreSQL ─────────
    if "postgres" in app.config["SQLALCHEMY_DATABASE_URI"]:
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "pool_timeout": 30,
            "connect_args": {
                "connect_timeout": 10,
            },
        }

    # Initialisation des extensions
    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = "admin.login"
    login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."

    # Import des routes
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")

    # ─────────────────────────────────────────
    # Scheduler (scraping automatique)
    # ─────────────────────────────────────────
    if not scheduler.running:
        from app.scrapers.runner import run_all_scrapers

        def scraper_job():
            with app.app_context():
                run_all_scrapers()

        scheduler.add_job(
            func=scraper_job,
            trigger="interval",
            hours=24,
            id="daily_scraper",
            replace_existing=True,
        )

        scheduler.start()

    # ─────────────────────────────────────────
    # Création des tables + admin
    # ─────────────────────────────────────────
    with app.app_context():
        db.create_all()
        _create_admin()

    return app


def _create_admin():
    import os
    from app.models.event import Admin

    admin_username = os.environ.get("ADMIN_USERNAME", "admin")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@univdz.dz")

    if not Admin.query.filter_by(username=admin_username).first():
        admin = Admin(username=admin_username, email=admin_email)
        admin.set_password(admin_password)

        db.session.add(admin)
        db.session.commit()