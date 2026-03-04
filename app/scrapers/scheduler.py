import logging
import random
import requests

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

SITE_URL = "https://univdz.onrender.com/"


def keep_alive():
    """Pinger le site toutes les 10min pour éviter la mise en veille Render."""
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        r = requests.get(SITE_URL, headers=headers, timeout=10)
        logger.info(f"[KeepAlive] ✅ Ping OK — Status: {r.status_code}")
    except Exception as e:
        logger.warning(f"[KeepAlive] ⚠️ Ping échoué : {e}")


def schedule_jobs(scheduler, app):

    # ─── JOB 1 : Scraping toutes les 12h ──────────────────────
    def scraping_job():
        from app.scrapers.runner import run_all_scrapers
        try:
            logger.info("[Scheduler] 🚀 Lancement du scraping automatique...")
            run_all_scrapers(app)
            logger.info("[Scheduler] ✅ Scraping terminé.")
        except Exception as e:
            logger.error(f"[Scheduler] ❌ Erreur scraping : {e}")

    scheduler.add_job(
        func=scraping_job,
        trigger="interval",
        hours=12,
        id="scraping_automatique",
        replace_existing=True,
    )

    # ─── JOB 2 : Keep-Alive toutes les 10 minutes ─────────────
    scheduler.add_job(
        func=keep_alive,
        trigger="interval",
        minutes=10,
        id="keep_alive",
        replace_existing=True,
    )

    logger.info("[Scheduler] ✅ Jobs planifiés : scraping (12h) + keep-alive (10min)")