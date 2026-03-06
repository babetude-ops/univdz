import logging
import re
from datetime import date
from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

NEWS_PATHS = [
    "/actualites",
    "/fr/actualites",
    "/index.php/actualites",
    "/fr/index.php/actualites",
    "/actualite",
    "/news",
    "/fr/news",
    "/evenements",
    "/fr/evenements",
    "/manifestations-scientifiques",
    "/fr/manifestations-scientifiques",
    "/activites-scientifiques",
    "/appels",
    "/bourses",
]

BOURSE_KEYWORDS = [
    "bourse", "scholarship", "fellowship", "erasmus", "mobilité",
    "appel à candidature", "programme de bourse", "financement"
]

EVENT_KEYWORDS = [
    "colloque", "séminaire", "conférence", "journée", "atelier",
    "workshop", "appel à communication", "manifestation", "symposium"
]


def parse_date(text):
    m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", text)
    if m:
        try:
            d = int(m.group(1))
            mth = int(m.group(2))
            y = int(m.group(3))
            return date(y, mth, d)
        except:
            return None
    return None


class GenericUnivScraper(BaseScraper):

    def __init__(self, site_name, base_url, news_path, universite, wilaya):
        self.site_name = site_name
        self.base_url = base_url.rstrip("/")
        self.news_path = news_path
        self.universite = universite
        self.wilaya = wilaya

    def scrape(self) -> list[dict]:

        results = []

        url = self.base_url + self.news_path

        soup = self.fetch(url)

        if not soup:
            return []

        links = soup.find_all("a", href=True)

        seen = set()

        for link in links:

            titre = link.get_text(strip=True)

            href = link["href"]

            if not titre or len(titre) < 10 or len(titre) > 400:
                continue

            if len(titre) > 200:
                continue

            titre_lower = titre.lower()

            is_relevant = any(
                kw in titre_lower for kw in BOURSE_KEYWORDS + EVENT_KEYWORDS
            )

            if not is_relevant:
                continue

            if titre in seen:
                continue

            seen.add(titre)

            # filtrage des dates passées
            event_date = parse_date(titre)

            if event_date and event_date < date.today():
                continue

            if href.startswith("http"):
                lien = href
            elif href.startswith("/"):
                lien = self.base_url + href
            else:
                lien = self.base_url + "/" + href

            results.append({
                "titre": titre,
                "institution": self.universite,
                "wilaya": self.wilaya,
                "lien_officiel": lien,
                "source_url": url,
            })

        logger.info(f"[{self.site_name}] {len(results)} résultats trouvés")

        return results


class SmartUnivScraper(GenericUnivScraper):

    def __init__(self, site_name, base_url, universite, wilaya, preferred_path=None):
        self.site_name = site_name
        self.base_url = base_url.rstrip("/")
        self.universite = universite
        self.wilaya = wilaya
        self.news_path = preferred_path or "/actualites"

    def scrape(self) -> list[dict]:

        paths_to_try = [self.news_path] + [p for p in NEWS_PATHS if p != self.news_path]

        for path in paths_to_try:

            url = self.base_url + path

            soup = self.fetch(url)

            if soup:

                self.news_path = path

                logger.info(f"[{self.site_name}] URL trouvée: {url}")

                return super().scrape()

        logger.warning(f"[{self.site_name}] Aucun chemin valide trouvé")

        return []


def get_all_scrapers():

    universities = [

        ("Université d'Alger 1 Benyoucef Benkhedda", "https://www.univ-alger.dz", "Alger"),
        ("Université d'Alger 2 Abou El Kacem Saadallah", "https://www.univ-alger2.dz", "Alger"),
        ("Université d'Alger 3 Ibrahim Sultan Cheibout", "https://www.univ-alger3.dz", "Alger"),
        ("USTHB", "https://www.usthb.dz", "Alger"),
        ("École Nationale Polytechnique", "https://www.enp.edu.dz", "Alger"),
        ("ESI Alger", "https://www.esi.dz", "Alger"),

        ("Université d'Oran 1 Ahmed Ben Bella", "https://www.univ-oran1.dz", "Oran"),
        ("Université d'Oran 2 Mohamed Ben Ahmed", "https://www.univ-oran2.dz", "Oran"),

        ("Université de Mostaganem Abdelhamid Ibn Badis", "https://www.univ-mosta.dz", "Mostaganem"),

        ("Université de Tlemcen Abou Bekr Belkaid", "https://www.univ-tlemcen.dz", "Tlemcen"),

        ("Université de Béjaïa Abderrahmane Mira", "https://www.univ-bejaia.dz", "Béjaïa"),

        ("Université de Tizi Ouzou Mouloud Mammeri", "https://www.ummto.dz", "Tizi Ouzou"),

        ("Université de Sétif 1 Ferhat Abbas", "https://www.univ-setif.dz", "Sétif"),

        ("Université Constantine 1 Frères Mentouri", "https://www.umc.edu.dz", "Constantine"),

        ("Université d'Annaba Badji Mokhtar", "https://www.univ-annaba.dz", "Annaba"),

        ("Université de Batna 1 Hadj Lakhdar", "https://www.univ-batna.dz", "Batna"),

        ("Université de Biskra Mohamed Khider", "https://www.univ-biskra.dz", "Biskra"),

        ("Université de Laghouat Amar Telidji", "https://www.lagh-univ.dz", "Laghouat"),

        ("Université de Ouargla Kasdi Merbah", "https://www.univ-ouargla.dz", "Ouargla"),

        ("Université d'Adrar Ahmed Draia", "http://www.univ-adrar.dz", "Adrar"),

        ("Université d'El Oued Hamma Lakhdar", "https://www.univ-eloued.dz", "El Oued"),

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


class BejaiaSpecificScraper(GenericUnivScraper):

    def __init__(self):

        super().__init__(
            site_name="Université de Béjaïa",
            base_url="https://www.univ-bejaia.dz",
            news_path="/vrrelex/fr/actualites",
            universite="Université Abderrahmane Mira de Béjaïa",
            wilaya="Béjaïa"
        )


class USThBScraper(SmartUnivScraper):

    def __init__(self):

        super().__init__(
            site_name="USTHB",
            base_url="https://www.usthb.dz",
            universite="Université des Sciences et de la Technologie Houari Boumediene",
            wilaya="Alger",
        )


class UniOran1Scraper(SmartUnivScraper):

    def __init__(self):

        super().__init__(
            site_name="Université Oran 1",
            base_url="https://www.univ-oran1.dz",
            universite="Université d'Oran 1 Ahmed Ben Bella",
            wilaya="Oran",
        )


class UniConstantine1Scraper(SmartUnivScraper):

    def __init__(self):

        super().__init__(
            site_name="Université Constantine 1",
            base_url="https://www.umc.edu.dz",
            universite="Université Frères Mentouri Constantine 1",
            wilaya="Constantine",
        )