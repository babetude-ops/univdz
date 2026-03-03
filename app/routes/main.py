from flask import Blueprint, render_template, request, abort
from app.models.event import Event
from app import db
from sqlalchemy import or_

main_bp = Blueprint("main", __name__)

EVENTS_PER_PAGE = 12

WILAYAS = [
    "Adrar","Chlef","Laghouat","Oum El Bouaghi","Batna","Béjaïa","Biskra",
    "Béchar","Blida","Bouira","Tamanrasset","Tébessa","Tlemcen","Tiaret",
    "Tizi Ouzou","Alger","Djelfa","Jijel","Sétif","Saïda","Skikda",
    "Sidi Bel Abbès","Annaba","Guelma","Constantine","Médéa","Mostaganem",
    "M'Sila","Mascara","Ouargla","Oran","El Bayadh","Illizi","Bordj Bou Arréridj",
    "Boumerdès","El Tarf","Tindouf","Tissemsilt","El Oued","Khenchela",
    "Souk Ahras","Tipaza","Mila","Aïn Defla","Naâma","Aïn Témouchent",
    "Ghardaïa","Relizane","Timimoun","Bordj Badji Mokhtar","Ouled Djellal",
    "Béni Abbès","In Salah","In Guezzam","Touggourt","Djanet","El M'Ghair","El Meniaa",
]

EVENT_TYPES = ["colloque", "séminaire", "journée_etude", "appel_communication", "bourse", "atelier", "conférence"]

DISCIPLINES = [
    "Sciences exactes", "Sciences de la nature", "Sciences médicales",
    "Sciences humaines", "Sciences sociales", "Droit", "Économie",
    "Informatique", "Mathématiques", "Physique", "Chimie",
    "Lettres et langues", "Histoire", "Géographie", "Philosophie",
    "Architecture", "Ingénierie", "Sciences agronomiques", "Autre",
]


@main_bp.route("/")
def index():
    upcoming = (
        Event.query.filter_by(statut="valide")
        .order_by(Event.date_debut.asc())
        .limit(6)
        .all()
    )
    bourses = (
        Event.query.filter_by(statut="valide", type="bourse")
        .order_by(Event.date_limite.asc())
        .limit(4)
        .all()
    )
    stats = {
        "total": Event.query.filter_by(statut="valide").count(),
        "bourses": Event.query.filter_by(statut="valide", type="bourse").count(),
        "colloques": Event.query.filter_by(statut="valide", type="colloque").count(),
    }
    return render_template(
        "main/index.html",
        upcoming=upcoming,
        bourses=bourses,
        stats=stats,
        wilayas=WILAYAS,
        event_types=EVENT_TYPES,
        disciplines=DISCIPLINES,
    )


@main_bp.route("/evenements")
def evenements():
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "")
    type_filtre = request.args.get("type", "")
    wilaya_filtre = request.args.get("wilaya", "")
    discipline_filtre = request.args.get("discipline", "")
    date_debut_filtre = request.args.get("date_debut", "")

    query = Event.query.filter_by(statut="valide")

    if q:
        query = query.filter(
            or_(
                Event.titre.ilike(f"%{q}%"),
                Event.description.ilike(f"%{q}%"),
                Event.universite.ilike(f"%{q}%"),
            )
        )
    if type_filtre:
        query = query.filter_by(type=type_filtre)
    if wilaya_filtre:
        query = query.filter_by(wilaya=wilaya_filtre)
    if discipline_filtre:
        query = query.filter_by(discipline=discipline_filtre)
    if date_debut_filtre:
        from datetime import datetime
        try:
            d = datetime.strptime(date_debut_filtre, "%Y-%m-%d").date()
            query = query.filter(Event.date_debut >= d)
        except ValueError:
            pass

    pagination = query.order_by(Event.date_debut.asc()).paginate(
        page=page, per_page=EVENTS_PER_PAGE, error_out=False
    )

    return render_template(
        "main/evenements.html",
        events=pagination.items,
        pagination=pagination,
        wilayas=WILAYAS,
        event_types=EVENT_TYPES,
        disciplines=DISCIPLINES,
        current_filters={
            "q": q,
            "type": type_filtre,
            "wilaya": wilaya_filtre,
            "discipline": discipline_filtre,
            "date_debut": date_debut_filtre,
        },
    )


@main_bp.route("/evenement/<slug>")
def detail(slug):
    event = Event.query.filter_by(slug=slug, statut="valide").first_or_404()
    similaires = (
        Event.query.filter(
            Event.statut == "valide",
            Event.type == event.type,
            Event.id != event.id,
        )
        .limit(3)
        .all()
    )
    return render_template("main/detail.html", event=event, similaires=similaires)


@main_bp.route("/bourses")
def bourses():
    bourses_list = (
        Event.query.filter_by(statut="valide", type="bourse")
        .order_by(Event.date_limite.asc())
        .all()
    )
    return render_template("main/bourses.html", bourses=bourses_list)


@main_bp.route("/sitemap.xml")
def sitemap():
    from flask import make_response
    events = Event.query.filter_by(statut="valide").all()
    xml = render_template("main/sitemap.xml", events=events)
    response = make_response(xml)
    response.headers["Content-Type"] = "application/xml"
    return response
@main_bp.route("/revues")
def revues():
    from app.models.event import Revue
    domaine_filtre = request.args.get("domaine", "")
    
    query = Revue.query.filter_by(statut="valide")
    if domaine_filtre:
        query = query.filter_by(domaine=domaine_filtre)
    
    revues_list = query.order_by(Revue.date_collecte.desc()).all()
    
    # Grouper par domaine
    domaines = {}
    for r in revues_list:
        d = r.domaine or "Autre"
        if d not in domaines:
            domaines[d] = []
        domaines[d].append(r)
    
    tous_domaines = Revue.query.filter_by(statut="valide").with_entities(Revue.domaine).distinct().all()
    tous_domaines = [d[0] for d in tous_domaines if d[0]]
    
    return render_template(
        "main/revues.html",
        domaines=domaines,
        tous_domaines=tous_domaines,
        domaine_filtre=domaine_filtre,
        total=len(revues_list),
    )


@main_bp.route("/revue/<slug>")
def detail_revue(slug):
    from app.models.event import Revue
    revue = Revue.query.filter_by(slug=slug, statut="valide").first_or_404()
    similaires = Revue.query.filter(
        Revue.statut == "valide",
        Revue.domaine == revue.domaine,
        Revue.id != revue.id,
    ).limit(4).all()
    return render_template("main/detail_revue.html", revue=revue, similaires=similaires)