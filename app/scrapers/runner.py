import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.scrapers.universities import USThBScraper, UniOran1Scraper, UniConstantine1Scraper, GenericUnivScraper
from app.scrapers.mesrs import MESRSScraper

logger = logging.getLogger(__name__)

SCRAPERS = [
    USThBScraper(),
    UniOran1Scraper(),
    UniConstantine1Scraper(),
    GenericUnivScraper(
        site_name="Université Béjaïa",
        base_url="https://www.univ-bejaia.dz",
        news_paths=["/univ-actualites", "/actualites", "/fr/actualites"],
        universite="Université Abderrahmane Mira de Béjaïa",
        wilaya="Béjaïa",
    ),
    GenericUnivScraper(
        site_name="Université Sétif 1",
        base_url="https://www.univ-setif.dz",
        news_paths=["/actualites", "/fr/actualites"],
        universite="Université Ferhat Abbas Sétif 1",
        wilaya="Sétif",
    ),
]


def run_scraper(scraper, app):
    """Lancer un scraper individuel — utilisé par le thread pool."""
    try:
        count = scraper.run(app)
        logger.info(f"[Runner] ✅ {scraper.site_name}: {count} événements")
        return count
    except Exception as e:
        logger.error(f"[Runner] ❌ Erreur {scraper.site_name}: {e}")
        return 0


def run_all_scrapers(app=None) -> int:
    from flask import current_app
    _app = app or current_app._get_current_object()
    total = 0

    logger.info(f"[Runner] 🚀 Lancement — {len(SCRAPERS)} universités...")

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(run_scraper, scraper, _app): scraper.site_name
            for scraper in SCRAPERS
        }
        for future in as_completed(futures):
            total += future.result()

    try:
        mesrs = MESRSScraper()
        count = mesrs.run(_app)
        total += count
        logger.info(f"[Runner] ✅ MESRS: {count} bourses")
    except Exception as e:
        logger.error(f"[Runner] ❌ Erreur MESRS: {e}")

    try:
        from app.scrapers.asjp import ASJPScraper
        asjp = ASJPScraper()
        count = asjp.run_revues(_app)
        total += count
        logger.info(f"[Runner] ✅ ASJP: {count} revues")
    except Exception as e:
        logger.error(f"[Runner] ❌ Erreur ASJP: {e}")

    logger.info(f"[Runner] 🏁 Total collecté: {total}")
    return total

