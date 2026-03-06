import logging
from urllib.parse import urljoin
from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

BOURSE_KEYWORDS = [
    "bourse",
    "bourses",
    "appel",
    "appel à candidature",
    "appel a candidature",
]

EVENT_KEYWORDS = [
    "colloque",
    "séminaire",
    "seminaire",
    "conférence",
    "conference",
    "manifestation",
    "journée",
    "journee",
]


class UniversityScraper(BaseScraper):

    universite = ""
    wilaya = ""

    def scrape(self):

        results = []
        seen = set()

        soup = self.fetch(self.base_url)

        if not soup:
            return []

        candidate_pages = []

        # détecter pages importantes
        for a in soup.find_all("a", href=True):

            text = a.get_text(strip=True).lower()

            if any(k in text for k in [
                "actualité",
                "actualite",
                "news",
                "événement",
                "evenement",
                "manifestation",
                "colloque",
                "séminaire",
                "appel",
                "bourse"
            ]):

                link = urljoin(self.base_url, a["href"])
                candidate_pages.append(link)

        candidate_pages = list(set(candidate_pages))[:5]

        logger.info(f"[{self.site_name}] pages détectées: {len(candidate_pages)}")

        for page in candidate_pages:

            page_soup = self.fetch(page)

            if not page_soup:
                continue

            for link in page_soup.find_all("a", href=True):

                titre = link.get_text(strip=True)

                if not titre or len(titre) < 10:
                    continue

                titre_lower = titre.lower()

                if not any(k in titre_lower for k in BOURSE_KEYWORDS + EVENT_KEYWORDS):
                    continue

                if titre in seen:
                    continue

                seen.add(titre)

                lien = urljoin(self.base_url, link["href"])

                results.append({
                    "titre": titre,
                    "institution": self.universite,
                    "wilaya": self.wilaya,
                    "lien_officiel": lien,
                    "source_url": page,
                })

        logger.info(f"[{self.site_name}] {len(results)} résultats trouvés")

        return results


# universités test
UNIVERSITIES = [

    ("Université Alger 1", "https://www.univ-alger.dz", "Alger"),
    ("Université Alger 2", "https://www.univ-alger2.dz", "Alger"),
    ("Université Alger 3", "https://www.univ-alger3.dz", "Alger"),
    ("USTHB", "https://www.usthb.dz", "Alger"),
    ("ESI Alger", "https://www.esi.dz", "Alger"),

    ("Université Oran 1", "https://www.univ-oran1.dz", "Oran"),
    ("Université Mostaganem", "https://www.univ-mosta.dz", "Mostaganem"),
    ("Université Bejaia", "https://www.univ-bejaia.dz", "Bejaia"),

    ("Université Setif 1", "https://www.univ-setif.dz", "Setif"),
    ("Université Constantine 1", "https://www.umc.edu.dz", "Constantine"),
]


def get_all_scrapers():

    scrapers = []

    for name, url, wilaya in UNIVERSITIES:

        scraper = UniversityScraper()

        scraper.site_name = name
        scraper.base_url = url
        scraper.universite = name
        scraper.wilaya = wilaya

        scrapers.append(scraper)

    return scrapers