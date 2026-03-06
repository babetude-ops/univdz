import logging
from app.scrapers.base import BaseScraper
from app.utils.ai_classifier import classify_event

logger = logging.getLogger(__name__)

EVENT_KEYWORDS = [
    "colloque",
    "séminaire",
    "seminaire",
    "conference",
    "conférence",
    "workshop",
    "appel",
    "communication",
    "bourse",
    "scholarship",
    "erasmus",
    "mobilité",
    "manifestation",
    "symposium"
]


class SmartUnivScraper(BaseScraper):

    def __init__(self, site_name, base_url, universite, wilaya):
        self.site_name = site_name
        self.base_url = base_url.rstrip("/")
        self.universite = universite
        self.wilaya = wilaya

    def scrape(self) -> list[dict]:

        results = []
        seen = set()

        soup = self.fetch(self.base_url)

        if not soup:
            return []

        candidate_pages = []

        # détecter pages événements
        for a in soup.find_all("a", href=True):

            text = a.get_text(strip=True).lower()
            href = a["href"]

            if any(k in text for k in EVENT_KEYWORDS):

                if href.startswith("http"):
                    link = href
                elif href.startswith("/"):
                    link = self.base_url + href
                else:
                    link = self.base_url + "/" + href

                candidate_pages.append(link)

        logger.info(f"[{self.site_name}] pages détectées: {len(candidate_pages)}")

        for page in candidate_pages[:5]:

            page_soup = self.fetch(page)

            if not page_soup:
                continue

            for link in page_soup.find_all("a", href=True):

                href = link["href"]

                # détecter documents scientifiques
                if href.endswith(".pdf") or href.endswith(".doc") or href.endswith(".docx"):
                    titre = link.get_text(strip=True) or href
                else:
                    titre = link.get_text(strip=True)

                if not titre or len(titre) < 10 or len(titre) > 300:
                    continue

                if titre in seen:
                    continue

                seen.add(titre)

                titre_lower = titre.lower()

                # filtrage avant IA
                if not any(k in titre_lower for k in EVENT_KEYWORDS):
                    continue

                # classification IA
                type_event = classify_event(titre)

                if href.startswith("http"):
                    lien = href
                elif href.startswith("/"):
                    lien = self.base_url + href
                else:
                    lien = self.base_url + "/" + href

                results.append({
                    "titre": titre,
                    "type": type_event,
                    "institution": self.universite,
                    "wilaya": self.wilaya,
                    "lien_officiel": lien,
                    "source_url": page,
                })

        logger.info(f"[{self.site_name}] {len(results)} résultats trouvés")

        return results


def get_all_scrapers():

    universities = [

        ("Université d'Alger 1", "https://www.univ-alger.dz", "Alger"),
        ("Université d'Alger 2", "https://www.univ-alger2.dz", "Alger"),
        ("Université d'Alger 3", "https://www.univ-alger3.dz", "Alger"),
        ("USTHB", "https://www.usthb.dz", "Alger"),
        ("ESI Alger", "https://www.esi.dz", "Alger"),

        ("Université Oran 1", "https://www.univ-oran1.dz", "Oran"),
        ("Université Oran 2", "https://www.univ-oran2.dz", "Oran"),

        ("Université Mostaganem", "https://www.univ-mosta.dz", "Mostaganem"),
        ("Université Tlemcen", "https://www.univ-tlemcen.dz", "Tlemcen"),
        ("Université Sidi Bel Abbes", "https://www.univ-sba.dz", "Sidi Bel Abbes"),

        ("Université Béjaïa", "https://www.univ-bejaia.dz", "Bejaia"),
        ("Université Tizi Ouzou", "https://www.ummto.dz", "Tizi Ouzou"),

        ("Université Sétif 1", "https://www.univ-setif.dz", "Setif"),
        ("Université Sétif 2", "https://www.univ-setif2.dz", "Setif"),

        ("Université Constantine 1", "https://www.umc.edu.dz", "Constantine"),
        ("Université Constantine 2", "https://www.univ-constantine2.dz", "Constantine"),

        ("Université Annaba", "https://www.univ-annaba.dz", "Annaba"),
        ("Université Guelma", "https://www.univ-guelma.dz", "Guelma"),
        ("Université Skikda", "https://www.univ-skikda.dz", "Skikda"),

        ("Université Batna 1", "https://www.univ-batna.dz", "Batna"),
        ("Université Batna 2", "https://www.univ-batna2.dz", "Batna"),

        ("Université Biskra", "https://www.univ-biskra.dz", "Biskra"),
        ("Université Djelfa", "https://www.univ-djelfa.dz", "Djelfa"),

        ("Université Laghouat", "https://www.lagh-univ.dz", "Laghouat"),
        ("Université Ouargla", "https://www.univ-ouargla.dz", "Ouargla"),

        ("Université Adrar", "http://www.univ-adrar.dz", "Adrar"),
        ("Université El Oued", "https://www.univ-eloued.dz", "El Oued"),

        ("Université Souk Ahras", "https://www.univ-soukahras.dz", "Souk Ahras"),
        ("Université Tebessa", "https://www.univ-tebessa.dz", "Tebessa"),
        ("Université Oum El Bouaghi", "https://www.univ-oeb.dz", "Oum El Bouaghi"),

    ]

    scrapers = []

    for name, url, wilaya in universities:

        scrapers.append(
            SmartUnivScraper(
                site_name=name,
                base_url=url,
                universite=name,
                wilaya=wilaya,
            )
        )

    return scrapers