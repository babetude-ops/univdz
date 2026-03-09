import re
import time
import logging
from datetime import datetime
from typing import List, Dict

import requests
from bs4 import BeautifulSoup
from slugify import slugify

from app import db
from app.models.event import Revue
from app.scrapers.revues_asjp import REVUES_ASJP

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

APPEL_KEYWORDS = [
    "appel à contribution",
    "appel à soumission",
    "call for paper",
    "call for papers",
    "soumission",
    "submit",
    "submission",
    "appel à article",
]

DOMAINES = {
    "droit": "Droit",
    "law": "Droit",
    "économie": "Économie",
    "economic": "Économie",
    "gestion": "Gestion",
    "management": "Gestion",
    "informatique": "Informatique",
    "computer": "Informatique",
    "science": "Sciences",
    "engineering": "Ingénierie",
    "médecine": "Médecine",
    "medicine": "Médecine",
}


def detect_domain(text: str):

    text = text.lower()

    for key, val in DOMAINES.items():
        if key in text:
            return val

    return "Autres"


def extract_deadline(text: str):

    match = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})", text)

    if match:
        try:
            return datetime.strptime(match.group(1), "%d/%m/%Y").date()
        except Exception:
            pass

    return None


class ASJPScraper:

    def fetch(self, url):

        try:

            r = requests.get(url, headers=HEADERS, timeout=20)

            if r.status_code == 200:
                return BeautifulSoup(r.text, "html.parser")

        except Exception as e:

            logger.error(f"[ASJP] fetch error {url}: {e}")

        return None


    def get_calls_for_papers(self, journal):

        soup = self.fetch(journal["url"])

        if not soup:
            return None

        text = soup.get_text(" ").lower()

        has_call = any(keyword in text for keyword in APPEL_KEYWORDS)

        if not has_call:
            return None

        description = soup.get_text(" ", strip=True)[:1500]

        domaine = detect_domain(description)

        deadline = extract_deadline(text)

        slug = slugify(journal["nom"])

        if Revue.query.filter_by(slug=slug).first():
            return None

        revue = Revue(
            nom=journal["nom"],
            domaine=domaine,
            universite="",
            description=description,
            lien_officiel=journal["url"],
            lien_asjp=journal["url"],
            date_limite=deadline,
            statut_appel="ouvert",
            source="ASJP",
            score_fiabilite=0.8,
            statut="valide",
            slug=slug
        )

        db.session.add(revue)
        db.session.commit()

        return revue.to_dict()


    def scrape(self) -> List[Dict]:

        logger.info(f"[ASJP] {len(REVUES_ASJP)} revues à analyser")

        revues = []

        for i, journal in enumerate(REVUES_ASJP):

            try:

                result = self.get_calls_for_papers(journal)

                if result:
                    revues.append(result)

                    logger.info(f"[ASJP] appel ouvert: {journal['nom']}")

                # pause pour éviter blocage serveur
                if i % 5 == 0:
                    time.sleep(1)

            except Exception as e:

                logger.error(f"[ASJP] erreur {journal['url']} : {e}")

        logger.info(f"[ASJP] {len(revues)} revues avec appel ouvert")

        return revues


    def run_revues(self, app):

        with app.app_context():

            results = self.scrape()

        return len(results)
