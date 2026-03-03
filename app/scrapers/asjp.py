"""
Scraper ASJP — Algerian Scientific Journal Platform
Détecte les revues ayant publié un appel à soumission.
https://www.asjp.cerist.dz
"""
import re
import logging
from datetime import datetime
from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

DOMAINES_KEYWORDS = {
    "Sciences exactes et naturelles": ["mathématique", "physique", "chimie", "biologie", "sciences exactes", "astronomie"],
    "Sciences de la vie": ["médecine", "pharmacie", "vétérinaire", "santé", "biochimie", "sciences de la vie"],
    "Sciences de la terre": ["géologie", "géographie", "environnement", "sciences de la terre", "hydraulique"],
    "Sciences de l'ingénieur": ["génie", "électronique", "mécanique", "informatique", "technologie", "ingénieur"],
    "Sciences humaines": ["histoire", "philosophie", "archéologie", "sciences humaines", "patrimoine"],
    "Sciences sociales": ["sociologie", "psychologie", "anthropologie", "sciences sociales", "démographie"],
    "Droit et sciences politiques": ["droit", "juridique", "sciences politiques", "relations internationales"],
    "Économie et gestion": ["économie", "gestion", "finance", "comptabilité", "management", "commerce"],
    "Lettres et langues": ["littérature", "linguistique", "langue", "traduction", "lettres", "arabe", "français"],
    "Sciences islamiques": ["islamique", "fiqh", "charia", "coran", "hadith", "sciences islamiques"],
    "Arts et architecture": ["arts", "architecture", "urbanisme", "design", "beaux-arts"],
    "Sciences de l'éducation": ["éducation", "pédagogie", "didactique", "formation", "enseignement"],
}


def detect_domaine(texte: str) -> str:
    texte = texte.lower()
    for domaine, keywords in DOMAINES_KEYWORDS.items():
        if any(kw in texte for kw in keywords):
            return domaine
    return "Autre"


class ASJPScraper(BaseScraper):
    site_name = "ASJP"
    base_url = "https://www.asjp.cerist.dz"

    APPEL_KEYWORDS = [
        "appel à soumission", "appel à contribution", "call for paper",
        "soumettre", "soumission", "numéro en cours", "en cours de publication",
        "accepte les soumissions", "dépôt des articles",
    ]

    def scrape(self) -> list[dict]:
        revues = []

        # Page principale des revues
        soup = self.fetch(f"{self.base_url}/en/revues")
        if not soup:
            logger.warning("[ASJP] Impossible d'accéder à la page des revues")
            return revues

        # Chercher tous les liens de revues
        liens_revues = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/en/revues/" in href or "/ar/revues/" in href:
                if href not in liens_revues:
                    liens_revues.append(href)

        logger.info(f"[ASJP] {len(liens_revues)} revues trouvées")

        # Visiter chaque revue
        for lien in liens_revues[:50]:  # Limiter à 50 pour ne pas surcharger
            try:
                url = lien if lien.startswith("http") else self.base_url + lien
                revue_data = self._scrape_revue(url)
                if revue_data:
                    revues.append(revue_data)
            except Exception as e:
                logger.error(f"[ASJP] Erreur revue {lien}: {e}")

        logger.info(f"[ASJP] {len(revues)} revues avec appel à soumission")
        return revues

    def _scrape_revue(self, url: str) -> dict | None:
        soup = self.fetch(url)
        if not soup:
            return None

        # Nom de la revue
        nom_tag = soup.find("h1") or soup.find("h2") or soup.find(class_=re.compile(r"title|nom|name"))
        if not nom_tag:
            return None
        nom = nom_tag.get_text(strip=True)
        if len(nom) < 5:
            return None

        # Vérifier s'il y a un appel à soumission
        page_text = soup.get_text().lower()
        has_appel = any(kw in page_text for kw in self.APPEL_KEYWORDS)
        if not has_appel:
            return None

        # Description / résumé
        description = ""
        desc_tag = soup.find(class_=re.compile(r"description|about|resume|summary"))
        if desc_tag:
            description = desc_tag.get_text(strip=True)[:500]

        # Université / institution
        universite = ""
        univ_tag = soup.find(string=re.compile(r"université|institution|établissement", re.I))
        if univ_tag and univ_tag.parent:
            universite = univ_tag.parent.get_text(strip=True)[:200]

        # Détecter le domaine
        domaine = detect_domaine(nom + " " + description)

        # Date limite si mentionnée
        date_limite = None
        date_match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", page_text)
        if date_match:
            try:
                from datetime import date
                d, m, y = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
                if 2024 <= y <= 2027:
                    date_limite = date(y, m, d)
            except Exception:
                pass

        return {
            "nom": nom[:500],
            "domaine": domaine,
            "description": description,
            "universite": universite[:300],
            "lien_asjp": url,
            "lien_officiel": url,
            "date_limite": date_limite,
            "statut_appel": "ouvert",
            "source": "ASJP",
        }

    def run_revues(self, app) -> int:
        """Version spéciale pour sauvegarder des Revue et non des Event."""
        from app import db
        from app.models.event import Revue
        from slugify import slugify

        count = 0
        with app.app_context():
            raw_list = self.scrape()
            for raw in raw_list:
                try:
                    # Vérifier doublon
                    exists = Revue.query.filter_by(lien_asjp=raw.get("lien_asjp")).first()
                    if exists:
                        continue

                    # Générer slug unique
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
                        statut_appel=raw.get("statut_appel", "ouvert"),
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