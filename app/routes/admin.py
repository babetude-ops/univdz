from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from app.models.event import Admin, Event
from app import db

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))
    if request.method == "POST":
        user = Admin.query.filter_by(username=request.form.get("username")).first()
        if user and user.check_password(request.form.get("password")):
            login_user(user, remember=True)
            return redirect(url_for("admin.dashboard"))
        flash("Identifiants incorrects.", "danger")
    return render_template("admin/login.html")


@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@admin_bp.route("/")
@login_required
def dashboard():
    stats = {
        "a_verifier": Event.query.filter_by(statut="a_verifier").count(),
        "valide": Event.query.filter_by(statut="valide").count(),
        "rejete": Event.query.filter_by(statut="rejete").count(),
    }
    recents = Event.query.filter_by(statut="a_verifier").order_by(Event.date_collecte.desc()).limit(10).all()
    return render_template("admin/dashboard.html", stats=stats, recents=recents)


@admin_bp.route("/queue")
@login_required
def queue():
    page = request.args.get("page", 1, type=int)
    events = Event.query.filter_by(statut="a_verifier").order_by(Event.date_collecte.desc()).paginate(page=page, per_page=20)
    return render_template("admin/queue.html", events=events)


@admin_bp.route("/valider/<int:event_id>", methods=["POST"])
@login_required
def valider(event_id):
    event = Event.query.get_or_404(event_id)
    event.statut = "valide"
    event.date_validation = datetime.utcnow()
    event.validated_by = current_user.id
    db.session.commit()
    flash(f'Événement "{event.titre[:50]}" validé.', "success")
    return redirect(request.referrer or url_for("admin.queue"))


@admin_bp.route("/rejeter/<int:event_id>", methods=["POST"])
@login_required
def rejeter(event_id):
    event = Event.query.get_or_404(event_id)
    event.statut = "rejete"
    event.date_validation = datetime.utcnow()
    event.validated_by = current_user.id
    db.session.commit()
    flash(f'Événement "{event.titre[:50]}" rejeté.', "warning")
    return redirect(request.referrer or url_for("admin.queue"))


@admin_bp.route("/editer/<int:event_id>", methods=["GET", "POST"])
@login_required
def editer(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == "POST":
        event.titre = request.form.get("titre", event.titre)
        event.type = request.form.get("type", event.type)
        event.universite = request.form.get("universite", event.universite)
        event.discipline = request.form.get("discipline", event.discipline)
        event.wilaya = request.form.get("wilaya", event.wilaya)
        event.description = request.form.get("description", event.description)
        event.lien_officiel = request.form.get("lien_officiel", event.lien_officiel)
        db.session.commit()
        flash("Événement mis à jour.", "success")
        return redirect(url_for("admin.queue"))
    return render_template("admin/editer.html", event=event)


@admin_bp.route("/scraper/lancer", methods=["POST"])
@login_required
def lancer_scraper():
    from app.scrapers.runner import run_all_scrapers
    try:
        count = run_all_scrapers()
        flash(f"{count} événement(s) collecté(s) et ajouté(s) à la file.", "success")
    except Exception as e:
        flash(f"Erreur lors du scraping : {str(e)}", "danger")
    return redirect(url_for("admin.dashboard"))
@admin_bp.route("/revues/valider/<int:revue_id>", methods=["POST"])
@login_required
def valider_revue(revue_id):
    from app.models.event import Revue
    revue = Revue.query.get_or_404(revue_id)
    revue.statut = "valide"
    revue.date_validation = datetime.utcnow()
    revue.validated_by = current_user.id
    db.session.commit()
    flash(f'Revue "{revue.nom[:50]}" validée.', "success")
    return redirect(request.referrer or url_for("admin.dashboard"))


@admin_bp.route("/revues/rejeter/<int:revue_id>", methods=["POST"])
@login_required
def rejeter_revue(revue_id):
    from app.models.event import Revue
    revue = Revue.query.get_or_404(revue_id)
    revue.statut = "rejete"
    revue.date_validation = datetime.utcnow()
    revue.validated_by = current_user.id
    db.session.commit()
    flash(f'Revue "{revue.nom[:50]}" rejetée.', "warning")
    return redirect(request.referrer or url_for("admin.dashboard"))


@admin_bp.route("/scraper/asjp", methods=["POST"])
@login_required
def lancer_scraper_asjp():
    from app.scrapers.asjp import ASJPScraper
    try:
        scraper = ASJPScraper()
        count = scraper.run_revues(current_app._get_current_object())
        flash(f"{count} revue(s) ASJP collectée(s).", "success")
    except Exception as e:
        flash(f"Erreur ASJP : {str(e)}", "danger")
    return redirect(url_for("admin.dashboard"))