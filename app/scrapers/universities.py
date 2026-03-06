import logging
import re
from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# Chemins communs à tester pour les actualités
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


class GenericUnivScraper(BaseScraper):
    """Scraper générique pour les universités algériennes."""

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

        # Chercher les liens pertinents
        links = soup.find_all("a", href=True)
        seen = set()

        for link in links:
            titre = link.get_text(strip=True)
            href = link["href"]

            if not titre or len(titre) < 10 or len(titre) > 400:
                continue

            # Filtrer le bruit (menus, nav)
            if len(titre) > 200:
                continue

            titre_lower = titre.lower()
            is_relevant = any(kw in titre_lower for kw in BOURSE_KEYWORDS + EVENT_KEYWORDS)

            if not is_relevant:
                continue

            if titre in seen:
                continue
            seen.add(titre)

            # Construire l'URL complète
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
    """Scraper intelligent qui teste plusieurs chemins."""

    def __init__(self, site_name, base_url, universite, wilaya, preferred_path=None):
        self.site_name = site_name
        self.base_url = base_url.rstrip("/")
        self.universite = universite
        self.wilaya = wilaya
        self.news_path = preferred_path or "/actualites"

    def scrape(self) -> list[dict]:
        # Essayer le chemin préféré d'abord
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


# ─────────────────────────────────────────────────
# Liste complète des universités algériennes
# ─────────────────────────────────────────────────

def get_all_scrapers():
    """Retourne la liste de tous les scrapers universitaires."""
    universities = [
        # Alger
        ("Université d'Alger 1 Benyoucef Benkhedda", "https://www.univ-alger.dz", "Alger"),
        ("Université d'Alger 2 Abou El Kacem Saadallah", "https://www.univ-alger2.dz", "Alger"),
        ("Université d'Alger 3 Ibrahim Sultan Cheibout", "https://www.univ-alger3.dz", "Alger"),
        ("USTHB", "https://www.usthb.dz", "Alger"),
        ("École Nationale Polytechnique", "https://www.enp.edu.dz", "Alger"),
        ("ESI Alger", "https://www.esi.dz", "Alger"),
        ("ENSA Alger", "https://www.ensa.dz", "Alger"),

        # Oran
        ("Université d'Oran 1 Ahmed Ben Bella", "https://www.univ-oran1.dz", "Oran"),
        ("Université d'Oran 2 Mohamed Ben Ahmed", "https://www.univ-oran2.dz", "Oran"),
        ("ESI Sidi Abdellah", "https://www.esi-sba.dz", "Oran"),

        # Mostaganem
        ("Université de Mostaganem Abdelhamid Ibn Badis", "https://www.univ-mosta.dz", "Mostaganem"),

        # Tlemcen
        ("Université de Tlemcen Abou Bekr Belkaid", "https://www.univ-tlemcen.dz", "Tlemcen"),

        # Sidi Bel Abbès
        ("Université de Sidi Bel Abbès Djillali Liabes", "https://www.univ-sba.dz", "Sidi Bel Abbès"),

        # Chlef
        ("Université de Chlef Hassiba Benbouali", "https://www.univ-chlef.dz", "Chlef"),

        # Béjaïa
        ("Université de Béjaïa Abderrahmane Mira", "https://www.univ-bejaia.dz", "Béjaïa"),

        # Tizi Ouzou
        ("Université de Tizi Ouzou Mouloud Mammeri", "https://www.ummto.dz", "Tizi Ouzou"),

        # Sétif
        ("Université de Sétif 1 Ferhat Abbas", "https://www.univ-setif.dz", "Sétif"),
        ("Université de Sétif 2 Mohamed Lamine Debaghine", "https://www.univ-setif2.dz", "Sétif"),

        # Constantine
        ("Université Constantine 1 Frères Mentouri", "https://www.umc.edu.dz", "Constantine"),
        ("Université Constantine 2 Abdelhamid Mehri", "https://www.univ-constantine2.dz", "Constantine"),
        ("Université Constantine 3 Salah Boubnider", "https://www.univ-constantine3.dz", "Constantine"),
        ("École Nationale Supérieure de Biotechnologie", "https://www.ensb.dz", "Constantine"),

        # Annaba
        ("Université d'Annaba Badji Mokhtar", "https://www.univ-annaba.dz", "Annaba"),

        # Guelma
        ("Université de Guelma 8 Mai 1945", "https://www.univ-guelma.dz", "Guelma"),

        # Skikda
        ("Université de Skikda 20 Août 1955", "https://www.univ-skikda.dz", "Skikda"),

        # Batna
        ("Université de Batna 1 Hadj Lakhdar", "https://www.univ-batna.dz", "Batna"),
        ("Université de Batna 2 Mostefa Ben Boulaid", "https://www.univ-batna2.dz", "Batna"),
        ("École Nationale Supérieure Énergies Renouvelables", "https://www.ens-er.dz", "Batna"),

        # Biskra
        ("Université de Biskra Mohamed Khider", "https://www.univ-biskra.dz", "Biskra"),

        # Djelfa
        ("Université de Djelfa Ziane Achour", "https://www.univ-djelfa.dz", "Djelfa"),

        # Laghouat
        ("Université de Laghouat Amar Telidji", "https://www.lagh-univ.dz", "Laghouat"),

        # Ouargla
        ("Université de Ouargla Kasdi Merbah", "https://www.univ-ouargla.dz", "Ouargla"),

        # Adrar
        ("Université d'Adrar Ahmed Draia", "http://www.univ-adrar.dz", "Adrar"),

        # El Oued
        ("Université d'El Oued Hamma Lakhdar", "https://www.univ-eloued.dz", "El Oued"),

        # Khenchela
        ("Université de Khenchela Abbes Laghrour", "https://www.univ-khenchela.dz", "Khenchela"),

        # Souk Ahras
        ("Université de Souk Ahras Mohamed Cherif Messaadia", "https://www.univ-soukahras.dz", "Souk Ahras"),

        # Tébessa
        ("Université de Tébessa Larbi Tebessi", "https://www.univ-tebessa.dz", "Tébessa"),

        # Oum El Bouaghi
        ("Université d'Oum El Bouaghi Larbi Ben M'hidi", "https://www.univ-oeb.dz", "Oum El Bouaghi"),

        # Bordj Bou Arréridj
        ("Université de Bordj Bou Arréridj Mohamed Bachir El Ibrahimi", "https://www.univ-bba.dz", "Bordj Bou Arréridj"),

        # Médéa
        ("Université de Médéa Yahia Fares", "https://www.univ-medea.dz", "Médéa"),

        # Blida
        ("Université de Blida 1 Saad Dahlab", "https://www.univ-blida.dz", "Blida"),
        ("Université de Blida 2 Lounici Ali", "https://www.univ-blida2.dz", "Blida"),

        # Bouira
        ("Université de Bouira Akli Mohand Oulhadj", "https://www.univ-bouira.dz", "Bouira"),

        # Tamanrasset
        ("Université de Tamanrasset", "https://www.univ-tamanrasset.dz", "Tamanrasset"),

        # Ghardaïa
        ("Université de Ghardaïa", "https://www.univ-ghardaia.dz", "Ghardaïa"),

        # Mascara
        ("Université de Mascara Mustapha Stambouli", "https://www.univ-mascara.dz", "Mascara"),

        # Relizane
        ("Université de Relizane Ahmed Zabana", "https://www.univ-relizane.dz", "Relizane"),

        # Saïda
        ("Université de Saïda Dr Moulay Tahar", "https://www.univ-saida.dz", "Saïda"),

        # Centres universitaires
        ("Centre Universitaire de Tissemsilt", "https://www.cu-tissemsilt.dz", "Tissemsilt"),
        ("Centre Universitaire d'Aïn Témouchent", "https://www.cu-at.dz", "Aïn Témouchent"),
        ("Centre Universitaire de Tipaza", "https://www.cu-tipaza.dz", "Tipaza"),
        ("Centre Universitaire de Mila", "https://www.cu-mila.dz", "Mila"),
        ("Centre Universitaire de Naâma", "https://www.cu-naama.dz", "Naâma"),
        ("Centre Universitaire d'El Bayadh", "https://www.cu-elbayadh.dz", "El Bayadh"),
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


# Scrapers spécifiques avec chemins connus
class BejaiaSpecificScraper(GenericUnivScraper):
    def __init__(self):
        super().__init__(
            site_name="Université de Béjaïa",
            base_url="https://www.univ-bejaia.dz",
            news_path="/vrrelex/fr/actualites",
            universite="Université Abderrahmane Mira de Béjaïa",
            wilaya="Béjaïa"
        )


# Compatibilité avec ancien code
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
