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

    from config.settings import config
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = "admin.login"
    login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."

    from app.routes.main import main_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")

    if not scheduler.running:
        from app.scrapers.scheduler import schedule_jobs
        schedule_jobs(scheduler, app)
        scheduler.start()

    return app