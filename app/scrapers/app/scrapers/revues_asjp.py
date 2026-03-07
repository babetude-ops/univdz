# app/scrapers/revues_asjp.py

"""
Liste statique des revues ASJP.

Chaque entrée contient :
- nom : nom générique de la revue (ID ASJP)
- url : URL de la page de présentation de la revue sur ASJP

Le scraper vérifiera ensuite si la page existe réellement et
si un appel à contribution est présent.
"""

ASJP_BASE_URL = "https://www.asjp.cerist.dz/en/PresentationRevue/"

REVUES_ASJP = [
    {"nom": f"Revue ASJP {i}", "url": f"{ASJP_BASE_URL}{i}"}
    for i in range(1, 901)
]