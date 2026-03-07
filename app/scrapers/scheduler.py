from apscheduler.schedulers.background import BackgroundScheduler
from app.scrapers.runner import run_all_scrapers
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def schedule_jobs():
    """
    Lance automatiquement le scraper chaque jour.
    """

    scheduler.add_job(
        func=run_all_scrapers,
        trigger="interval",
        hours=24,
        id="daily_scraper",
        replace_existing=True,
    )

    scheduler.start()

    logger.info("Scheduler démarré : scraper automatique toutes les 24h")