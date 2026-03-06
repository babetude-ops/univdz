import logging
from app.scrapers.universities import get_all_scrapers
from app.scrapers.mesrs import MESRSScraper

logger = logging.getLogger(__name__)


def run_all_scrapers(app=None) -> int:

    from flask import current_app

    _app = app or current_app._get_current_object()

    total = 0

    # ─── Scraper toutes les universités ─────────────────────
    for scraper in get_all_scrapers():

        try:

            count = scraper.run(_app)

            total += count

            if count > 0:
                logger.info(f"[Runner] {scraper.site_name}: {count} opportunités")

        except Exception as e:

            logger.error(f"[Runner] Erreur {scraper.site_name}: {e}")

    # ─── Scraper MESRS ──────────────────────────────────────
    try:

        mesrs = MESRSScraper()

        count = mesrs.run(_app)

        total += count

        logger.info(f"[Runner] MESRS: {count} opportunités")

    except Exception as e:

        logger.error(f"[Runner] Erreur MESRS: {e}")

    # ─── Scraper ASJP ───────────────────────────────────────
    try:

        from app.scrapers.asjp import ASJPScraper

        asjp = ASJPScraper()

        count = asjp.run_revues(_app)

        total += count

        logger.info(f"[Runner] ASJP: {count} revues")

    except Exception as e:

        logger.error(f"[Runner] Erreur ASJP: {e}")

    logger.info(f"[Runner] Total collecté: {total}")

    return total