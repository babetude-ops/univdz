import re
from app.scrapers.base import BaseScraper


class USThBScraper(BaseScraper):
    site_name = "USTHB"
    base_url = "https://www.usthb.dz"
    KEYWORDS = ["colloque", "séminaire", "journée", "conférence", "appel", "communication"]

    def scrape(self) -> list[dict]:
        events = []
        for path in ["/actualites", "/fr/actualites", "/news"]:
            soup = self.fetch(f"{self.base_url}{path}")
            if soup:
                break
        if not soup:
            return events
        articles = soup.find_all("article") or soup.find_all("div", class_=re.compile(r"post|news|event"))
        for article in articles:
            title_tag = article.find(["h2", "h3", "h4"])
            if not title_tag:
                continue
            titre = title_tag.get_text(strip=True)
            if not any(kw in titre.lower() for kw in self.KEYWORDS):
                continue
            link_tag = article.find("a", href=True)
            lien = link_tag["href"] if link_tag else None
            if lien and not lien.startswith("http"):
                lien = self.base_url + lien
            description_tag = article.find("p")
            description = description_tag.get_text(strip=True) if description_tag else ""
            events.append({"titre": titre, "description": description, "lien_officiel": lien, "universite": "USTHB", "wilaya": "Alger"})
        return events


class UniOran1Scraper(BaseScraper):
    site_name = "Université Oran 1"
    base_url = "https://www.univ-oran1.dz"

    def scrape(self) -> list[dict]:
        events = []
        for path in ["/actualites", "/index.php/actualites", "/fr/actualites"]:
            soup = self.fetch(f"{self.base_url}{path}")
            if soup:
                break
        if not soup:
            return events
        for item in soup.select(".item-list li, .view-content .views-row, article"):
            titre_tag = item.find(["h3", "h2", "a"])
            if not titre_tag:
                continue
            titre = titre_tag.get_text(strip=True)
            if len(titre) < 10:
                continue
            link_tag = item.find("a", href=True)
            lien = link_tag["href"] if link_tag else None
            if lien and not lien.startswith("http"):
                lien = self.base_url + lien
            events.append({"titre": titre, "lien_officiel": lien, "universite": "Université Oran 1", "wilaya": "Oran"})
        return events


class UniConstantine1Scraper(BaseScraper):
    site_name = "Université Constantine 1"
    base_url = "https://www.umc.edu.dz"

    def scrape(self) -> list[dict]:
        events = []
        for path in ["/fr/actualites", "/fr/actualites/actualites-umc", "/actualites"]:
            soup = self.fetch(f"{self.base_url}{path}")
            if soup:
                break
        if not soup:
            return events
        for item in soup.select(".actualite, .news-item, article, li.item"):
            titre_tag = item.find(["h3", "h2", "h4", "a"])
            if not titre_tag:
                continue
            titre = titre_tag.get_text(strip=True)
            if len(titre) < 10:
                continue
            link_tag = item.find("a", href=True)
            lien = link_tag["href"] if link_tag else None
            if lien and not lien.startswith("http"):
                lien = self.base_url + lien
            events.append({"titre": titre, "lien_officiel": lien, "universite": "Université Constantine 1", "wilaya": "Constantine"})
        return events


class GenericUnivScraper(BaseScraper):
    def __init__(self, site_name, base_url, news_paths, universite, wilaya):
        self.site_name = site_name
        self.base_url = base_url
        self.news_paths = news_paths if isinstance(news_paths, list) else [news_paths]
        self.universite = universite
        self.wilaya = wilaya

    def scrape(self) -> list[dict]:
        events = []
        soup = None
        for path in self.news_paths:
            url = self.base_url.rstrip("/") + "/" + path.lstrip("/")
            soup = self.fetch(url)
            if soup:
                break
        if not soup:
            return events
        KEYWORDS = ["colloque", "séminaire", "journée d'étude", "conférence", "appel", "communication", "bourse", "atelier"]
        for tag in soup.find_all(["h2", "h3", "h4", "li", "article"]):
            text = tag.get_text(strip=True)
            if len(text) < 15:
                continue
            if not any(kw in text.lower() for kw in KEYWORDS):
                continue
            link_tag = tag.find("a", href=True)
            lien = None
            if link_tag and link_tag.get("href"):
                lien = link_tag["href"]
                if not lien.startswith("http"):
                    lien = self.base_url.rstrip("/") + "/" + lien.lstrip("/")
            events.append({"titre": text[:400], "lien_officiel": lien, "universite": self.universite, "wilaya": self.wilaya})
        return events


ALGERIAN_UNIVERSITY_SCRAPERS = [
    GenericUnivScraper("Université Alger 1", "https://www.univ-alger.dz", ["actualites", "fr/actualites"], "Université Alger 1", "Alger"),
    GenericUnivScraper("Université Alger 2", "https://www.univ-alger2.dz", ["actualites", "fr/actualites"], "Université Alger 2", "Alger"),
    GenericUnivScraper("Université Alger 3", "https://www.univ-alger3.dz", ["actualites", "fr/actualites"], "Université Alger 3", "Alger"),
    GenericUnivScraper("Université Blida 1", "https://www.univ-blida.dz", ["actualites", "fr/actualites"], "Université Blida 1", "Blida"),
    GenericUnivScraper("Université Blida 2", "https://www.univ-blida2.dz", ["actualites", "fr/actualites"], "Université Blida 2", "Blida"),
    GenericUnivScraper("Université Tlemcen", "https://www.univ-tlemcen.dz", ["actualites", "fr/actualites"], "Université Tlemcen", "Tlemcen"),
    GenericUnivScraper("Université Bejaia", "https://www.univ-bejaia.dz", ["univ-actualites", "actualites"], "Université Bejaia", "Bejaia"),
    GenericUnivScraper("Université Setif 1", "https://www.univ-setif.dz", ["actualites", "fr/actualites"], "Université Setif 1", "Setif"),
    GenericUnivScraper("Université Setif 2", "https://www.univ-setif2.dz", ["actualites", "fr/actualites"], "Université Setif 2", "Setif"),
    GenericUnivScraper("Université Batna 1", "https://www.univ-batna.dz", ["actualites", "fr/actualites"], "Université Batna 1", "Batna"),
    GenericUnivScraper("Université Batna 2", "https://www.univ-batna2.dz", ["actualites", "fr/actualites"], "Université Batna 2", "Batna"),
    GenericUnivScraper("Université Biskra", "https://www.univ-biskra.dz", ["actualites", "fr/actualites"], "Université Biskra", "Biskra"),
    GenericUnivScraper("Université Ouargla", "https://www.univ-ouargla.dz", ["actualites", "fr/actualites"], "Université Ouargla", "Ouargla"),
    GenericUnivScraper("Université Mostaganem", "https://www.univ-mosta.dz", ["actualites", "fr/actualites"], "Université Mostaganem", "Mostaganem"),
    GenericUnivScraper("Université Chlef", "https://www.univ-chlef.dz", ["actualites", "fr/actualites"], "Université Chlef", "Chlef"),
    GenericUnivScraper("Université Mascara", "https://www.univ-mascara.dz", ["actualites", "fr/actualites"], "Université Mascara", "Mascara"),
]



