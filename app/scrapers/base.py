import logging
from abc import ABC, abstractmethod
import requests
from urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup

from app import db
from app.models.event import Event
from app.utils.normalizer import normalize_event, generate_slug

# Désactiver les warnings SSL
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; UnivDZBot/1.0; "
        "+https://univdz.dz/bot)"
    )
}


class BaseScraper(ABC):

    site_name: str = "inconnu"
    base_url: str = ""
    timeout: int = 15

    def fetch(self, url: str):

        try:
            resp = requests.get(
                url,
                headers=HEADERS,
                timeout=self.timeout,
                verify=False
            )

            resp.raise_for_status()

            resp.encoding = resp.apparent_encoding

            return BeautifulSoup(resp.text, "html.parser")

        except requests.RequestException as e:

            logger.warning(f"[{self.site_name}] Erreur fetch {url}: {e}")

            return None

    @abstractmethod
    def scrape(self) -> list[dict]:
        raise NotImplementedError

    def run(self, app) -> int:

        count = 0

        with app.app_context():

            raw_events = self.scrape()

            if not raw_events:
                return 0

            for raw in raw_events:

                try:

                    # Normalisation
                    event_data = normalize_event(raw, source=self.site_name)

                    if not event_data or not event_data.get("titre"):
                        continue

                    # ✅ VALIDATION AUTOMATIQUE
                    event_data["statut"] = "valide"

                    # Vérifier duplicata
                    if self._is_duplicate(event_data):
                        continue

                    event = Event(**event_data)

                    # Génération slug
                    event.slug = generate_slug(
                        event_data["titre"],
                        event_data.get("date_debut")
                    )

                    db.session.add(event)

                    count += 1

                except Exception as e:

                    logger.error(
                        f"[{self.site_name}] Erreur sauvegarde: {e}"
                    )

                    db.session.rollback()

            try:
                db.session.commit()
            except Exception as e:

                logger.error(
                    f"[{self.site_name}] Erreur commit DB: {e}"
                )

                db.session.rollback()

        return count

    def _is_duplicate(self, event_data: dict) -> bool:

        try:

            if event_data.get("lien_officiel"):

                if Event.query.filter_by(
                    lien_officiel=event_data["lien_officiel"]
                ).first():

                    return True

            if event_data.get("titre") and event_data.get("source"):

                if Event.query.filter_by(
                    titre=event_data["titre"],
                    source=event_data["source"]
                ).first():

                    return True

        except Exception as e:

            logger.warning(f"[{self.site_name}] erreur duplicate check: {e}")

        return False