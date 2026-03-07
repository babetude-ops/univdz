ASJP_BASE_URL = "https://www.asjp.cerist.dz/en/PresentationRevue/"

REVUES_ASJP = [
    {"nom": f"Revue ASJP {i}", "url": f"{ASJP_BASE_URL}{i}"}
    for i in range(1, 901)
]