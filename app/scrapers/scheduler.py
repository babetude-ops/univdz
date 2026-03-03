import logging

logger = logging.getLogger(__name__)


def schedule_jobs(scheduler, app):
    def scraping_job():
        from app.scrapers.runner import run_all_scrapers
        try:
            run_all_scrapers(app)
        except Exception as e:
            logger.error(f"[Scheduler] Erreur : {e}")

    scheduler.add_job(
        func=scraping_job,
        trigger="interval",
        hours=12,
        id="scraping_automatique",
        replace_existing=True,
    )