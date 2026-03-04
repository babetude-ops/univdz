"""
Scraper MESRS — Ministère de l'Enseignement Supérieur et de la Recherche Scientifique
Adapté de Manus + intégration Flask UnivDZ
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

DATE_FORMATS = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y"]

BOURSE_KEYWORDS = [
    "bourse", "scholarship", "fellowship", "financement",
    "allocation", "mobilité", "coopération", "programme",
]

EVENT_KEYWORDS = [
    "colloque", "séminaire", "conférence", "journée d'étude",
    "atelier", "workshop", "forum", "symposium", "appel à communication",
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


def parse_date(texte: str) -> Optional[date]:
    # Format JJ/MM/AAAA
    m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", texte)
    if m:
        try:
            d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if 2024 <= y <= 2028 and 1 <= mo <= 12 and 1 <= d <= 31:
                return date(y, mo, d)
        except Exception:
            pass
    # Format JJ mois AAAA
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
    """Scraper MESRS — bourses + événements."""

    BASE_URL = "https://www.mesrs.dz"
    TIMEOUT = 20

    URLS_BOURSES = [
        "/index.php/fr/cooperation-interuniversitaire/",
        "/index.php/fr/bourses-et-allocations/",
        "/fr/bourses",
        "/bourses",
    ]

    URLS_ACTUALITES = [
        "/index.php/fr/actualites/",
        "/index.php/fr/",
        "/fr/actualites",
        "/actualites",
    ]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; UnivDZBot/1.0)"
        })

    def fetch(self, url: str) -> Optional[BeautifulSoup]:
        try:
            resp = self.session.get(url, timeout=self.TIMEOUT)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            logger.warning(f"[MESRS] Erreur fetch {url}: {e}")
            return None

    # ─── BOURSES ──────────────────────────────────────────────

    def get_scholarships(self) -> List[Dict]:
        bourses = []
        seen = set()

        for path in self.URLS_BOURSES:
            url = self.BASE_URL + path
            soup = self.fetch(url)
            if not soup:
                continue

            # Méthode 1 : sections dédiées bourses
            sections = soup.find_all(
                ["div", "article"],
                class_=re.compile(r"scholarship|bourse|offer|item", re.I)
            )
            for section in sections:
                b = self._parse_bourse(section, url)
                if b and b.get("titre") and b["titre"] not in seen:
                    seen.add(b["titre"])
                    bourses.append(b)

            # Méthode 2 : liens avec mots-clés bourses
            for a in soup.find_all("a", href=True):
                text = a.get_text(strip=True)
                href = a.get("href", "")
                if any(kw in text.lower() for kw in BOURSE_KEYWORDS) and len(text) > 10:
                    full_url = href if href.startswith("http") else self.BASE_URL + href
                    if text not in seen:
                        seen.add(text)
                        # Visiter la page de détail
                        detail = self._scrape_bourse_detail(full_url, text)
                        if detail:
                            bourses.append(detail)

            time.sleep(1)

        logger.info(f"[MESRS] {len(bourses)} bourses trouvées")
        return bourses

    def _parse_bourse(self, section, source_url: str) -> Optional[Dict]:
        try:
            titre_tag = section.find(["h1", "h2", "h3", "h4", "strong"])
            if not titre_tag:
                return None
            titre = titre_tag.get_text(strip=True)
            if len(titre) < 5:
                return None

            texte = section.get_text()
            description = ""
            p = section.find("p")
            if p:
                description = p.get_text(strip=True)[:400]

            date_limite = parse_date(texte)

            montant = ""
            m = re.search(r"([\d,.]+)\s*(DA|€|USD|\$|EUR|DZD)", texte)
            if m:
                montant = f"{m.group(1)} {m.group(2)}"

            return {
                "titre": titre[:400],
                "description": description,
                "date_limite": date_limite,
                "montant": montant,
                "lien_officiel": source_url,
                "source": "MESRS",
                "type": "bourse",
                "wilaya": "National",
            }
        except Exception as e:
            logger.error(f"[MESRS] Erreur parse bourse: {e}")
            return None

    def _scrape_bourse_detail(self, url: str, titre: str) -> Optional[Dict]:
        soup = self.fetch(url)
        if not soup:
            return {
                "titre": titre[:400],
                "description": "",
                "date_limite": None,
                "lien_officiel": url,
                "source": "MESRS",
                "type": "bourse",
                "wilaya": "National",
            }

        texte = soup.get_text()
        description = ""
        p = soup.find("p")
        if p:
            description = p.get_text(strip=True)[:400]

        return {
            "titre": titre[:400],
            "description": description,
            "date_limite": parse_date(texte),
            "lien_officiel": url,
            "source": "MESRS",
            "type": "bourse",
            "wilaya": "National",
        }

    # ─── ÉVÉNEMENTS ───────────────────────────────────────────

    def get_events(self) -> List[Dict]:
        events = []
        seen = set()

        for path in self.URLS_ACTUALITES:
            url = self.BASE_URL + path
            soup = self.fetch(url)
            if not soup:
                continue

            # Méthode 1 : articles/actualités
            articles = soup.find_all(
                ["article", "div"],
                class_=re.compile(r"post|event|actualite|news|item", re.I)
            )
            for article in articles:
                e = self._parse_event(article, url)
                if e and e.get("titre") and e["titre"] not in seen:
                    seen.add(e["titre"])
                    events.append(e)

            # Méthode 2 : titres avec mots-clés événements
            for tag in soup.find_all(["h2", "h3", "h4", "a"]):
                text = tag.get_text(strip=True)
                if len(text) < 10:
                    continue
                text_lower = text.lower()
                if any(kw in text_lower for kw in EVENT_KEYWORDS):
                    if text not in seen:
                        seen.add(text)
                        link = tag if tag.name == "a" else tag.find("a")
                        href = link.get("href", url) if link else url
                        full_url = href if href.startswith("http") else self.BASE_URL + href

                        # Détecter le type
                        event_type = "conférence"
                        for kw, t in EVENT_TYPES.items():
                            if kw in text_lower:
                                event_type = t
                                break

                        events.append({
                            "titre": text[:400],
                            "description": "",
                            "type": event_type,
                            "lien_officiel": full_url,
                            "source": "MESRS",
                            "wilaya": "National",
                            "universite": "MESRS",
                        })

            time.sleep(1)

        logger.info(f"[MESRS] {len(events)} événements trouvés")
        return events

    def _parse_event(self, section, source_url: str) -> Optional[Dict]:
        try:
            titre_tag = section.find(["h1", "h2", "h3", "h4", "strong"])
            if not titre_tag:
                return None
            titre = titre_tag.get_text(strip=True)
            if len(titre) < 10:
                return None

            texte = section.get_text()
            text_lower = texte.lower()

            description = ""
            p = section.find("p")
            if p:
                description = p.get_text(strip=True)[:400]

            # Type événement
            event_type = "conférence"
            for kw, t in EVENT_TYPES.items():
                if kw in text_lower:
                    event_type = t
                    break

            # Dates
            date_debut = parse_date(texte)
            link = section.find("a", href=True)
            href = link.get("href", source_url) if link else source_url
            full_url = href if href.startswith("http") else self.BASE_URL + href

            return {
                "titre": titre[:400],
                "description": description,
                "type": event_type,
                "date_debut": date_debut,
                "lien_officiel": full_url,
                "source": "MESRS",
                "wilaya": "National",
                "universite": "MESRS",
            }
        except Exception as e:
            logger.error(f"[MESRS] Erreur parse event: {e}")
            return None

    # ─── RUNNER PRINCIPAL ─────────────────────────────────────

    def run(self, app) -> int:
        """Sauvegarder bourses + événements dans la base UnivDZ."""
        from app import db
        from app.models.event import Event
        from app.utils.normalizer import generate_slug

        count = 0
        with app.app_context():
            # Bourses
            for raw in self.get_scholarships():
                try:
                    if Event.query.filter_by(
                        titre=raw["titre"], source="MESRS"
                    ).first():
                        continue
                    slug = generate_slug(raw["titre"], raw.get("date_limite"))
                    event = Event(
                        titre=raw["titre"],
                        type="bourse",
                        description=raw.get("description", ""),
                        date_limite=raw.get("date_limite"),
                        lien_officiel=raw.get("lien_officiel", ""),
                        source="MESRS",
                        wilaya=raw.get("wilaya", "National"),
                        universite=raw.get("universite", "MESRS"),
                        statut="a_verifier",
                        score_fiabilite=0.7,
                        date_collecte=datetime.utcnow(),
                        slug=slug,
                    )
                    db.session.add(event)
                    count += 1
                except Exception as e:
                    logger.error(f"[MESRS] Erreur bourse: {e}")
                    db.session.rollback()

            # Événements
            for raw in self.get_events():
                try:
                    if Event.query.filter_by(
                        titre=raw["titre"], source="MESRS"
                    ).first():
                        continue
                    slug = generate_slug(raw["titre"], raw.get("date_debut"))
                    event = Event(
                        titre=raw["titre"],
                        type=raw.get("type", "conférence"),
                        description=raw.get("description", ""),
                        date_debut=raw.get("date_debut"),
                        lien_officiel=raw.get("lien_officiel", ""),
                        source="MESRS",
                        wilaya=raw.get("wilaya", "National"),
                        universite=raw.get("universite", "MESRS"),
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