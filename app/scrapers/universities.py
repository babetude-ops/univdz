import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .base import BaseScraper

logger = logging.getLogger(__name__)


KEYWORDS = [
    "actualite",
    "actualites",
    "news",
    "evenement",
    "evenements",
    "manifestation",
    "colloque",
    "seminaire",
    "appel",
    "bourse"
]


class UniversitiesScraper(BaseScraper):

    site_name = "Universités Algériennes"

    universities = [
        ("Université Alger 1", "https://www.univ-alger.dz"),
        ("Université Alger 2", "https://www.univ-alger2.dz"),
        ("Université Alger 3", "https://www.univ-alger3.dz"),
        ("USTHB", "https://www.usthb.dz"),
        ("Université Oran 1", "https://www.univ-oran1.dz"),
        ("Université Constantine 1", "https://www.umc.edu.dz"),
        ("Université Batna 1", "https://www.univ-batna.dz"),
        ("Université Biskra", "https://www.univ-biskra.dz"),
        ("Université Bejaia", "https://www.univ-bejaia.dz"),
        ("Université Mostaganem", "https://www.univ-mosta.dz"),
        ("Université Setif 1", "https://www.univ-setif.dz"),
        ("Université Laghouat", "https://www.lagh-univ.dz"),
    ]

    def scrape(self):

        events = []

        for name, base_url in self.universities:

            logger.info(f"Scraping {name}")

            soup = self.fetch(base_url)

            if not soup:
                continue

            links = self.detect_news_links(soup, base_url)

            for url in links:

                page = self.fetch(url)

                if not page:
                    continue

                items = page.select("a")

                for a in items:

                    title = a.get_text(strip=True)

                    if len(title) < 20:
                        continue

                    link = a.get("href")

                    if not link:
                        continue

                    link = urljoin(base_url, link)

                    events.append({
                        "titre": title,
                        "lien_officiel": link,
                        "source": name
                    })

        return events

    def detect_news_links(self, soup: BeautifulSoup, base_url):

        links = []

        for a in soup.select("a"):

            href = a.get("href")

            if not href:
                continue

            href_lower = href.lower()

            for keyword in KEYWORDS:

                if keyword in href_lower:

                    links.append(urljoin(base_url, href))

        return list(set(links))