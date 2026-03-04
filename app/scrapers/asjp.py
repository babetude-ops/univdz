"""
Scraper ASJP — Version améliorée
Combine la logique de détection d'URLs de Manus + notre intégration Flask
SSL verify désactivé car certificat ASJP expiré
Limité à 20 revues pour respecter la mémoire du plan gratuit Render
"""
import re
import logging
import time
import urllib3
from datetime import datetime, date
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

DOMAINES_KEYWORDS = {
    "Sciences exactes et naturelles": ["mathématique", "physique", "chimie", "biologie", "astronomie"],
    "Sciences de la vie": ["médecine", "pharmacie", "vétérinaire", "santé", "biochimie"],
    "Sciences de la terre": ["géologie", "géographie", "environnement", "hydraulique"],
    "Sciences de l'ingénieur": ["génie", "électronique", "mécanique", "informatique", "technologie"],
    "Sciences humaines": ["histoire", "philosophie", "archéologie", "patrimoine"],
    "Sciences sociales": ["sociologie", "psychologie", "anthropologie", "démographie"],
    "Droit et sciences politiques": ["droit", "juridique", "sciences politiques"],
    "Économie et gestion": ["économie", "gestion", "finance", "comptabilité", "management"],
    "Lettres et langues": ["littérature", "linguistique", "langue", "traduction", "lettres"],
    "Sciences islamiques": ["islamique", "fiqh", "charia", "coran", "hadith"],
    "Arts et architecture": ["arts", "architecture", "urbanisme", "design"],
    "Sciences de l'éducation": ["éducation", "pédagogie", "didactique", "formation"],
}

APPEL_KEYWORDS = [
    "appel à soumission", "appel à contribution", "call for paper",
    "call for papers", "soumettre", "soumission en cours",
    "numéro en cours", "accepte les soumissions", "dépôt des articles",
    "submit", "submission", "appel à articles",
]

MOIS_FR = {
    "janvier": 1, "février": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12,
}

DATE_FORMATS = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y"]


def detect_domaine(texte: str) -> str:
    texte = texte.lower()
    for domaine, keywords in DOMAINES_KEYWORDS.items():
        if any(kw in texte for kw in keywords):
            return domaine
    return "Autre"


def parse_date(date_str: str) -> Optional[date]:
    date_str_lower = date_str.lower()
    for mois, num in MOIS_FR.items():
        date_str_lower = date_str_lower.replace(mois, str(num).zfill(2))
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str_lower.strip(), fmt).date()
        except ValueError:
            continue
    return None


def extract_date(texte: str) -> Optional[date]:
    m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", texte)
    if m:
        try:
            d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if 2024 <= y <= 2028 and 1 <= mo <= 12 and 1 <= d <= 31:
                return date(y, mo, d)
        except Exception:
            pass
    m = re.search(
        r"(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})",
        texte.lower()
    )
    if m:
        try:
            return date(int(m.group(3)), MOIS_FR[m.group(2)], int(m.group(1)))
        except Exception:
            pass
    return None


class ASJPScraper(BaseScraper):
    site_name = "ASJP"
    base_url = "https://www.asjp.cerist.dz"
    timeout = 20

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; UnivDZBot/1.0)"
        })

    def fetch(self, url: str):
        try:
            resp = self.session.get(url, timeout=self.timeout, verify=False)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            logger.warning(f"[ASJP] Erreur fetch {url}: {e}")
            return None

    def get_all_journals(self) -> List[Dict]:
        journals = []
        seen = set()

        for path in ["/en/revues", "/Revues", "/ar/revues"]:
            soup = self.fetch(self.base_url + path)
            if not soup:
                continue

            for a in soup.find_all("a", href=re.compile(r"PresentationRevue/\d+")):
                name = a.get_text(strip=True)
                href = a.get("href", "")
                url = href if href.startswith("http") else self.base_url + href
                if url not in seen and name:
                    seen.add(url)
                    journals.append({"name": name, "url": url})

            for a in soup.find_all("a", href=re.compile(r"/revues/\d+")):
                name = a.get_text(strip=True)
                href = a.get("href", "")
                url = href if href.startswith("http") else self.base_url + href
                if url not in seen and name:
                    seen.add(url)
                    journals.append({"name": name, "url": url})

            time.sleep(1)

        logger.info(f"[ASJP] {len(journals)} revues trouvées")
        return journals

    def get_calls_for_papers(self, journal: Dict) -> Optional[Dict]:
        soup = self.fetch(journal["url"])
        if not soup:
            return None

        page_text = soup.get_text(separator=" ").lower()

        has_appel = any(kw in page_text for kw in APPEL_KEYWORDS)
        call_links = soup.find_all("a", href=re.compile(r"callForPapers|Appel", re.IGNORECASE))
        if call_links:
            has_appel = True

        if not has_appel:
            return None

        nom = journal["name"]
        if not nom:
            h = soup.find("h1") or soup.find("h2")
            nom = h.get_text(strip=True) if h else "Revue sans nom"

        description = ""
        for cls in ["description", "about", "resume", "presentation"]:
            tag = soup.find(class_=re.compile(cls, re.I))
            if tag:
                description = tag.get_text(strip=True)[:500]
                break

        universite = ""
        m = re.search(r"(université[^,\n]{5,60}|univ\.[^,\n]{5,40})", page_text, re.I)
        if m:
            universite = m.group(0).strip()[:200]

        date_limite = extract_date(page_text)

        return {
            "nom": nom[:500],
            "domaine": detect_domaine(nom + " " + description),
            "description": description,
            "universite": universite,
            "lien_asjp": journal["url"],
            "lien_officiel": journal["url"],
            "date_limite": date_limite,
            "statut_appel": "ouvert",
            "source": "ASJP",
        }

    def scrape(self) -> List[Dict]:
        revues = []
        journals = self.get_all_journals()

        # Limité à 20 revues pour respecter la mémoire plan gratuit Render
        for i, journal in enumerate(journals[:20]):
            try:
                result = self.get_calls_for_papers(journal)
                if result:
                    revues.append(result)
                    logger.info(f"[ASJP] ✅ {result['nom'][:50]}")
                if i % 5 == 0:
                    time.sleep(1)
            except Exception as e:
                logger.error(f"[ASJP] Erreur {journal['url']}: {e}")

        logger.info(f"[ASJP] {len(revues)} revues avec appel ouvert")
        return revues

    def run_revues(self, app) -> int:
        from app import db
        from app.models.event import Revue
        from slugify import slugify

        count = 0
        with app.app_context():
            for raw in self.scrape():
                try:
                    if Revue.query.filter_by(lien_asjp=raw.get("lien_asjp")).first():
                        continue
                    base_slug = slugify(raw["nom"][:80], separator="-")
                    slug = base_slug
                    counter = 1
                    while Revue.query.filter_by(slug=slug).first():
                        slug = f"{base_slug}-{counter}"
                        counter += 1
                    revue = Revue(
                        nom=raw["nom"],
                        domaine=raw.get("domaine", "Autre"),
                        description=raw.get("description", ""),
                        universite=raw.get("universite", ""),
                        lien_asjp=raw.get("lien_asjp", ""),
                        lien_officiel=raw.get("lien_officiel", ""),
                        date_limite=raw.get("date_limite"),
                        statut_appel="ouvert",
                        source="ASJP",
                        date_collecte=datetime.utcnow(),
                        statut="a_verifier",
                        slug=slug,
                    )
                    db.session.add(revue)
                    count += 1
                except Exception as e:
                    logger.error(f"[ASJP] Erreur sauvegarde: {e}")
                    db.session.rollback()
            db.session.commit()
        return count