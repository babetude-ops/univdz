import re
from datetime import datetime
from slugify import slugify

TYPE_KEYWORDS = {
    "colloque": ["colloque", "congrès"],
    "séminaire": ["séminaire", "seminar"],
    "journée_etude": ["journée d'étude", "journées d'étude"],
    "appel_communication": ["appel à communication", "appel à contribution", "call for paper"],
    "bourse": ["bourse", "scholarship", "fellowship"],
    "atelier": ["atelier", "workshop"],
    "conférence": ["conférence", "conference"],
}

DISCIPLINE_KEYWORDS = {
    "Informatique": ["informatique", "ia ", "intelligence artificielle", "data"],
    "Mathématiques": ["mathématique", "algèbre", "analyse"],
    "Physique": ["physique", "énergie", "optique"],
    "Chimie": ["chimie", "biochimie"],
    "Sciences médicales": ["médecine", "santé", "pharmacie"],
    "Sciences de la nature": ["biologie", "écologie", "environnement"],
    "Droit": ["droit", "juridique"],
    "Économie": ["économie", "finance", "gestion", "management"],
    "Sciences humaines": ["histoire", "philosophie"],
    "Sciences sociales": ["sociologie", "psychologie"],
    "Lettres et langues": ["littérature", "linguistique", "langue"],
    "Architecture": ["architecture", "urbanisme"],
    "Ingénierie": ["génie", "mécanique", "électronique"],
}


def detect_type(titre, description=""):
    text = (titre + " " + (description or "")).lower()
    for event_type, keywords in TYPE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return event_type
    return "autre"


def detect_discipline(titre, description=""):
    text = (titre + " " + (description or "")).lower()
    for discipline, keywords in DISCIPLINE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return discipline
    return "Autre"


def compute_score(event_data):
    score = 0.3
    if event_data.get("lien_officiel"): score += 0.2
    if event_data.get("date_debut"): score += 0.2
    if event_data.get("description") and len(event_data["description"]) > 50: score += 0.15
    if event_data.get("universite"): score += 0.1
    if event_data.get("wilaya"): score += 0.05
    return min(round(score, 2), 1.0)


def normalize_event(raw, source=""):
    titre = (raw.get("titre") or "").strip()
    description = (raw.get("description") or "").strip()
    event_type = raw.get("type") or detect_type(titre, description)
    discipline = raw.get("discipline") or detect_discipline(titre, description)
    normalized = {
        "titre": titre[:500],
        "type": event_type,
        "universite": (raw.get("universite") or "").strip()[:300],
        "discipline": discipline,
        "wilaya": (raw.get("wilaya") or "").strip()[:100],
        "date_debut": raw.get("date_debut"),
        "date_fin": raw.get("date_fin"),
        "date_limite": raw.get("date_limite"),
        "description": description,
        "lien_officiel": (raw.get("lien_officiel") or "").strip()[:1000],
        "source": source or raw.get("source", "")[:500],
        "date_collecte": datetime.utcnow(),
        "statut": "a_verifier",
    }
    normalized["score_fiabilite"] = compute_score(normalized)
    return normalized


def generate_slug(titre, date_debut=None):
    base = slugify(titre[:80], allow_unicode=False, separator="-")
    if date_debut:
        suffix = str(date_debut).replace("-", "")[:8]
        base = f"{base}-{suffix}"
    from app.models.event import Event
    slug = base
    counter = 1
    while Event.query.filter_by(slug=slug).first():
        slug = f"{base}-{counter}"
        counter += 1
    return slug