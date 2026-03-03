import logging
from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup
from app import db
from app.models.event import Event
from app.utils.normalizer import normalize_event, generate_slug

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
            resp = requests.get(url, headers=HEADERS, timeout=self.timeout)
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
            for raw in raw_events:
                try:
                    event_data = normalize_event(raw, source=self.site_name)
                    if self._is_duplicate(event_data):
                        continue
                    event = Event(**event_data)
                    event.slug = generate_slug(event_data["titre"], event_data.get("date_debut"))
                    db.session.add(event)
                    count += 1
                except Exception as e:
                    logger.error(f"[{self.site_name}] Erreur sauvegarde: {e}")
                    db.session.rollback()
            db.session.commit()
        return count

    def _is_duplicate(self, event_data: dict) -> bool:
        if event_data.get("lien_officiel"):
            if Event.query.filter_by(lien_officiel=event_data["lien_officiel"]).first():
                return True
        if event_data.get("titre") and event_data.get("source"):
            if Event.query.filter_by(titre=event_data["titre"], source=event_data["source"]).first():
                return True
        return False