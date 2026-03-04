"""
Scraper MESRS — Version corrigée
Encodage UTF-8 + sélection précise des articles
"""
import re
import logging
import time
from datetime import datetime, date
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

MOIS_FR = {
    "janvier": 1, "février": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12,
}

BOURSE_KEYWORDS = [
    "bourse", "scholarship", "fellowship", "financement",
    "allocation", "mobilité", "erasmus", "campus france",
    "coopération", "programme de bourse", "appel à candidature",
]

EVENT_KEYWORDS = [
    "colloque", "séminaire", "conférence", "journée d'étude",
    "atelier", "workshop", "forum", "symposium",
    "appel à communication", "journée nationale", "journée internationale",
]

EVENT_TYPES = {
    "colloque": "colloque",
    "séminaire": "séminaire",
    "conférence": "conférence",
    "journée d'étude": "journée_etude",
    "journée": "journée_etude",
    "atelier": "atelier",
    "workshop": "atelier",
    "forum": "conférence",
    "symposium": "colloque",
    "appel à communication": "appel_communication",
}

TITRES_IGNORER = [
    "enseignant", "etablissement", "étudiant", "accueil", "home",
    "menu", "navigation", "footer", "header", "recherche", "search",
    "connexion", "login", "contact", "plan du site", "sitemap",
    "activités ministérielles", "ministère", "actualités",
]


def is_titre_valide(titre: str) -> bool:
    if len(titre) < 15:
        return False
    titre_lower = titre.lower().strip()
    if any(t == titre_lower for t in TITRES_IGNORER):
        return False
    if any(titre_lower.startswith(t) for t in TITRES_IGNORER[:6]):
        return False
    return True


def parse_date(texte: str) -> Optional[date]:
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


class MESRSScraper:
    BASE_URL = "https://www.mesrs.dz"
    TIMEOUT = 25

    URLS_BOURSES = [
        "/index.php/fr/cooperation-interuniversitaire/bourses-et-allocations",
        "/index.php/fr/cooperation-interuniversitaire/",
        "/index.php/fr/bourses-et-allocations/",
    ]

    URLS_ACTUALITES = [
        "/index.php/fr/actualites/evenements",
        "/index.php/fr/actualites/colloques-et-seminaires",
        "/index.php/fr/actualites/",
    ]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "fr-FR,fr;q=0.9",
        })

    def fetch(self, url: str) -> Optional[BeautifulSoup]:
        try:
            resp = self.session.get(url, timeout=self.TIMEOUT)
            resp.raise_for_status()
            resp.encoding = "utf-8"
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            logger.warning(f"[MESRS] Erreur fetch {url}: {e}")
            return None

    def _extraire_articles(self, soup: BeautifulSoup, source_url: str) -> List[Dict]:
        articles = []

        conteneurs = (
            soup.find_all("div", class_=re.compile(r"items-row|item-page|blog|article|news", re.I)) or
            soup.find_all("article") or
            soup.find_all("div", class_=re.compile(r"item\b", re.I))
        )

        for conteneur in conteneurs:
            titre_tag = (
                conteneur.find("a", class_=re.compile(r"title|heading|link", re.I)) or
                conteneur.find(["h2", "h3", "h4"])
            )
            if not titre_tag:
                continue

            titre = titre_tag.get_text(strip=True)
            if not is_titre_valide(titre):
                continue

            lien_tag = conteneur.find("a", href=True)
            href = lien_tag.get("href", source_url) if lien_tag else source_url
            full_url = href if href.startswith("http") else self.BASE_URL + href

            description = ""
            intro = conteneur.find(class_=re.compile(r"intro|summary|description|body", re.I))
            if not intro:
                intro = conteneur.find("p")
            if intro:
                description = intro.get_text(strip=True)[:400]

            texte_complet = conteneur.get_text()
            date_trouvee = parse_date(texte_complet)

            articles.append({
                "titre": titre[:400],
                "description": description,
                "date": date_trouvee,
                "lien": full_url,
            })

        return articles

    def get_scholarships(self) -> List[Dict]:
        bourses = []
        seen = set()

        for path in self.URLS_BOURSES:
            url = self.BASE_URL + path
            soup = self.fetch(url)
            if not soup:
                continue

            articles = self._extraire_articles(soup, url)
            for art in articles:
                titre_lower = art["titre"].lower()
                if not any(kw in titre_lower for kw in BOURSE_KEYWORDS):
                    continue
                if art["titre"] in seen:
                    continue
                seen.add(art["titre"])
                bourses.append({
                    "titre": art["titre"],
                    "description": art["description"],
                    "date_limite": art["date"],
                    "lien_officiel": art["lien"],
                    "source": "MESRS",
                    "type": "bourse",
                    "wilaya": "National",
                    "universite": "MESRS",
                })

            for a in soup.find_all("a", href=True):
                texte = a.get_text(strip=True)
                if len(texte) < 15:
                    continue
                if not any(kw in texte.lower() for kw in BOURSE_KEYWORDS):
                    continue
                if texte in seen:
                    continue
                if not is_titre_valide(texte):
                    continue
                seen.add(texte)
                href = a.get("href", "")
                full_url = href if href.startswith("http") else self.BASE_URL + href
                bourses.append({
                    "titre": texte[:400],
                    "description": "",
                    "date_limite": None,
                    "lien_officiel": full_url,
                    "source": "MESRS",
                    "type": "bourse",
                    "wilaya": "National",
                    "universite": "MESRS",
                })

            time.sleep(1)

        logger.info(f"[MESRS] {len(bourses)} bourses trouvées")
        return bourses

    def get_events(self) -> List[Dict]:
        events = []
        seen = set()

        for path in self.URLS_ACTUALITES:
            url = self.BASE_URL + path
            soup = self.fetch(url)
            if not soup:
                continue

            articles = self._extraire_articles(soup, url)
            for art in articles:
                if art["titre"] in seen:
                    continue
                seen.add(art["titre"])

                event_type = "conférence"
                titre_lower = art["titre"].lower()
                for kw, t in EVENT_TYPES.items():
                    if kw in titre_lower:
                        event_type = t
                        break

                events.append({
                    "titre": art["titre"],
                    "description": art["description"],
                    "date_debut": art["date"],
                    "lien_officiel": art["lien"],
                    "type": event_type,
                    "source": "MESRS",
                    "wilaya": "National",
                    "universite": "MESRS",
                })

            time.sleep(1)

        logger.info(f"[MESRS] {len(events)} événements trouvés")
        return events

    def run(self, app) -> int:
        from app import db
        from app.models.event import Event
        from app.utils.normalizer import generate_slug

        count = 0
        with app.app_context():
            for raw in self.get_scholarships():
                try:
                    if Event.query.filter_by(titre=raw["titre"], source="MESRS").first():
                        continue
                    slug = generate_slug(raw["titre"], raw.get("date_limite"))
                    event = Event(
                        titre=raw["titre"],
                        type="bourse",
                        description=raw.get("description", ""),
                        date_limite=raw.get("date_limite"),
                        lien_officiel=raw.get("lien_officiel", ""),
                        source="MESRS",
                        wilaya="National",
                        universite="MESRS",
                        statut="a_verifier",
                        score_fiabilite=0.75,
                        date_collecte=datetime.utcnow(),
                        slug=slug,
                    )
                    db.session.add(event)
                    count += 1
                except Exception as e:
                    logger.error(f"[MESRS] Erreur bourse: {e}")
                    db.session.rollback()

            for raw in self.get_events():
                try:
                    if Event.query.filter_by(titre=raw["titre"], source="MESRS").first():
                        continue
                    slug = generate_slug(raw["titre"], raw.get("date_debut"))
                    event = Event(
                        titre=raw["titre"],
                        type=raw.get("type", "conférence"),
                        description=raw.get("description", ""),
                        date_debut=raw.get("date_debut"),
                        lien_officiel=raw.get("lien_officiel", ""),
                        source="MESRS",
                        wilaya="National",
                        universite="MESRS",
                        statut="a_verifier",
                        score_fiabilite=0.75,
                        date_collecte=datetime.utcnow(),
                        slug=slug,
                    )
                    db.session.add(event)
                    count += 1
                except Exception as e:
                    logger.error(f"[MESRS] Erreur event: {e}")
                    db.session.rollback()

            db.session.commit()
        return count