import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import logging
import time
import re
from datetime import datetime
from typing import List, Dict

import requests
from bs4 import BeautifulSoup
from slugify import slugify

from app import db
from app.models.event import Revue

logger = logging.getLogger(__name__)

ASJP_BASE_URL = "http://www.asjp.cerist.dz/en/PresentationRevue/"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# génération automatique de 900 revues
REVUES_ASJP = [
    {"nom": f"Revue ASJP {i}", "url": f"{ASJP_BASE_URL}{i}"}
    for i in range(1, 901)
]


APPEL_KEYWORDS = [
    "appel à contribution",
    "appel à soumission",
    "call for paper",
    "call for papers",
    "soumission",
    "submit",
    "submission",
]


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

            r = requests.get(
                url,
                headers=HEADERS,
                timeout=20,
                verify=False
            )

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

        deadline = extract_deadline(text)

        slug = slugify(journal["nom"])

        if Revue.query.filter_by(slug=slug).first():
            return None

        revue = Revue(
            nom=journal["nom"],
            domaine="Autres",
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

        revues = []

        logger.info(f"[ASJP] Scan de {len(REVUES_ASJP)} revues")

        for i, journal in enumerate(REVUES_ASJP):

            try:

                result = self.get_calls_for_papers(journal)

                if result:
                    revues.append(result)
                    logger.info(f"[ASJP] appel ouvert: {journal['nom']}")

                # ralentir le scraping
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
