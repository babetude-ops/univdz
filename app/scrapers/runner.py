import logging
from app.scrapers.universities import USThBScraper, UniOran1Scraper, UniConstantine1Scraper, GenericUnivScraper

logger = logging.getLogger(__name__)

SCRAPERS = [
    USThBScraper(),
    UniOran1Scraper(),
    UniConstantine1Scraper(),
    GenericUnivScraper(site_name="Université Béjaïa", base_url="https://www.univ-bejaia.dz", news_path="/fr/actualites", universite="Université Abderrahmane Mira de Béjaïa", wilaya="Béjaïa"),
    GenericUnivScraper(site_name="Université Sétif 1", base_url="https://www.univ-setif.dz", news_path="/actualites", universite="Université Ferhat Abbas Sétif 1", wilaya="Sétif"),
]


def run_all_scrapers(app=None) -> int:
    from flask import current_app
    _app = app or current_app._get_current_object()
    total = 0
    for scraper in SCRAPERS:
        try:
            count = scraper.run(_app)
            total += count
        except Exception as e:
            logger.error(f"[Runner] Erreur {scraper.site_name}: {e}")
    return total