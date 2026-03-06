import re
import logging
from datetime import date
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
    "atelier",
    "workshop",
    "symposium",
]

# Chemins à essayer pour chaque université
NEWS_PATHS = [
    "/actualites",
    "/fr/actualites",
    "/actualite",
    "/fr/actualite",
    "/news",
    "/fr/news",
    "/evenements",
    "/fr/evenements",
    "/manifestations",
    "/fr/manifestations",
    "/colloques",
    "/fr/colloques",
    "/seminaires",
    "/bourses",
    "/appels",
    "/univ-actualites",
    "/index.php/actualites",
    "/index.php/fr/actualites",
]

ANNEE_COURANTE = date.today().year

MOIS_FR = {
    "janvier": 1, "février": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12,
}


def is_expired(titre: str) -> bool:
    """Retourne True si l'événement est passé."""
    titre_lower = titre.lower()
    today = date.today()

    # Chercher une année dans le titre
    years = re.findall(r"\b(20\d{2})\b", titre_lower)
    for y in years:
        if int(y) < today.year:
            return True

    # Chercher une date dd/mm/yyyy
    m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](20\d{2})", titre_lower)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            event_date = date(y, mo, d)
            if event_date < today:
                return True
        except Exception:
            pass

    # Chercher mois + année (ex: mars 2025)
    m = re.search(
        r"(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(20\d{2})",
        titre_lower
    )
    if m:
        mois = MOIS_FR[m.group(1)]
        annee = int(m.group(2))
        if annee < today.year:
            return True
        if annee == today.year and mois < today.month:
            return True

    return False


class UniversityScraper(BaseScraper):

    universite = ""
    wilaya = ""
    news_paths = NEWS_PATHS

    def fetch_first_valid(self):
        """Essaie plusieurs chemins et retourne le premier qui marche."""
        # D'abord essayer la page principale
        soup = self.fetch(self.base_url)
        if soup:
            return soup, self.base_url

        # Ensuite essayer les chemins
        for path in self.news_paths:
            url = self.base_url.rstrip("/") + path
            soup = self.fetch(url)
            if soup:
                logger.info(f"[{self.site_name}] ✅ URL trouvée: {url}")
                return soup, url

        return None, None

    def scrape(self):

        results = []
        seen = set()

        soup, page_url = self.fetch_first_valid()

        if not soup:
            logger.warning(f"[{self.site_name}] ❌ Aucune URL accessible")
            return []

        candidate_pages = [page_url]

        # Détecter pages importantes depuis la page trouvée
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True).lower()
            if any(k in text for k in [
                "actualité", "actualite", "news", "événement", "evenement",
                "manifestation", "colloque", "séminaire", "appel", "bourse",
                "conférence", "atelier", "workshop"
            ]):
                link = urljoin(self.base_url, a["href"])
                if link not in candidate_pages:
                    candidate_pages.append(link)

        candidate_pages = list(set(candidate_pages))[:6]
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

                # Ignorer les événements passés
                if is_expired(titre):
                    logger.debug(f"[{self.site_name}] ⏭️ Expiré: {titre[:50]}")
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


# Liste des universités algériennes
UNIVERSITIES = [

    # Alger
    ("Université Alger 1", "https://www.univ-alger.dz", "Alger"),
    ("Université Alger 2", "https://www.univ-alger2.dz", "Alger"),
    ("Université Alger 3", "https://www.univ-alger3.dz", "Alger"),
    ("USTHB", "https://www.usthb.dz", "Alger"),
    ("ESI Alger", "https://www.esi.dz", "Alger"),

    # Oran
    ("Université Oran 1", "https://www.univ-oran1.dz", "Oran"),
    ("Université Oran 2", "https://www.univ-oran2.dz", "Oran"),
    ("Université Mostaganem", "https://www.univ-mosta.dz", "Mostaganem"),
    ("Université Tlemcen", "https://www.univ-tlemcen.dz", "Tlemcen"),

    # Est
    ("Université Bejaia", "https://www.univ-bejaia.dz", "Bejaia"),
    ("Université Setif 1", "https://www.univ-setif.dz", "Setif"),
    ("Université Setif 2", "https://www.univ-setif2.dz", "Setif"),
    ("Université Constantine 1", "https://www.umc.edu.dz", "Constantine"),
    ("Université Constantine 2", "https://www.univ-constantine2.dz", "Constantine"),
    ("Université Constantine 3", "https://www.univ-constantine3.dz", "Constantine"),
    ("Université Annaba", "https://www.univ-annaba.dz", "Annaba"),
    ("Université Batna 1", "https://www.univ-batna.dz", "Batna"),
    ("Université Batna 2", "https://www.univ-batna2.dz", "Batna"),
    ("Université Biskra", "https://www.univ-biskra.dz", "Biskra"),

    # Centre
    ("Université Blida 1", "https://www.univ-blida.dz", "Blida"),
    ("Université Blida 2", "https://www.univ-blida2.dz", "Blida"),
    ("Université Tizi Ouzou", "https://www.ummto.dz", "Tizi Ouzou"),
    ("Université Bouira", "https://www.univ-bouira.dz", "Bouira"),
    ("Université Médéa", "https://www.univ-medea.dz", "Médéa"),

    # Sud
    ("Université Ouargla", "https://www.univ-ouargla.dz", "Ouargla"),
    ("Université Ghardaia", "https://www.univ-ghardaia.dz", "Ghardaia"),
    ("Université Bechar", "https://www.univ-bechar.dz", "Bechar"),
    ("Université Tamanrasset", "https://www.univ-tam.dz", "Tamanrasset"),

    # Autres
    ("Université Chlef", "https://www.univ-chlef.dz", "Chlef"),
    ("Université Mascara", "https://www.univ-mascara.dz", "Mascara"),
    ("Université Sidi Bel Abbes", "https://www.univ-sba.dz", "Sidi Bel Abbes"),
    ("Université Jijel", "https://www.univ-jijel.dz", "Jijel"),
    ("Université Skikda", "https://www.univ-skikda.dz", "Skikda"),
    ("Université Guelma", "https://www.univ-guelma.dz", "Guelma"),
    ("Université Souk Ahras", "https://www.univ-soukahras.dz", "Souk Ahras"),
    ("Université Khenchela", "https://www.univ-khenchela.dz", "Khenchela"),
    ("Université Oum El Bouaghi", "https://www.univ-oeb.dz", "Oum El Bouaghi"),
    ("Université Msila", "https://www.univ-msila.dz", "Msila"),
    ("Université Djelfa", "https://www.univ-djelfa.dz", "Djelfa"),
    ("Université Laghouat", "https://www.univ-laghouat.dz", "Laghouat"),
    ("Université El Oued", "https://www.univ-eloued.dz", "El Oued"),
    ("Université Adrar", "https://www.univ-adrar.dz", "Adrar"),
    ("Université Illizi", "https://www.univ-illizi.dz", "Illizi"),
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