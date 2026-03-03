from flask import Blueprint, jsonify, request
from app.models.event import Event

api_bp = Blueprint("api", __name__)


@api_bp.route("/events")
def get_events():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    type_filtre = request.args.get("type")
    wilaya_filtre = request.args.get("wilaya")

    query = Event.query.filter_by(statut="valide")
    if type_filtre:
        query = query.filter_by(type=type_filtre)
    if wilaya_filtre:
        query = query.filter_by(wilaya=wilaya_filtre)

    pagination = query.order_by(Event.date_debut.asc()).paginate(page=page, per_page=per_page)
    return jsonify({
        "events": [e.to_dict() for e in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page,
    })


@api_bp.route("/events/<int:event_id>")
def get_event(event_id):
    event = Event.query.get_or_404(event_id)
    return jsonify(event.to_dict())