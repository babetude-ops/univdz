# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from app.models.event import Admin, Event
from app import db
import threading

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
    flash("Evenement valide.", "success")
    return redirect(request.referrer or url_for("admin.queue"))


@admin_bp.route("/rejeter/<int:event_id>", methods=["POST"])
@login_required
def rejeter(event_id):
    event = Event.query.get_or_404(event_id)
    event.statut = "rejete"
    event.date_validation = datetime.utcnow()
    event.validated_by = current_user.id
    db.session.commit()
    flash("Evenement rejete.", "warning")
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
        flash("Evenement mis a jour.", "success")
        return redirect(url_for("admin.queue"))
    return render_template("admin/editer.html", event=event)


@admin_bp.route("/scraper/lancer", methods=["POST"])
@login_required
def lancer_scraper():
    from app.scrapers.runner import run_all_scrapers
    app = current_app._get_current_object()

    def scraper_thread():
        try:
            run_all_scrapers(app)
        except Exception as e:
            app.logger.error("[Scraper] Erreur thread: %s", str(e))

    t = threading.Thread(target=scraper_thread, daemon=True)
    t.start()

    flash("Scraping lance en arriere-plan ! Revenez dans quelques minutes.", "success")
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
    flash("Revue validee.", "success")
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
    flash("Revue rejetee.", "warning")
    return redirect(request.referrer or url_for("admin.dashboard"))


@admin_bp.route("/scraper/asjp", methods=["POST"])
@login_required
def lancer_scraper_asjp():
    from app.scrapers.asjp import ASJPScraper
    app = current_app._get_current_object()

    def asjp_thread():
        try:
            scraper = ASJPScraper()
            scraper.run_revues(app)
        except Exception as e:
            app.logger.error("[ASJP] Erreur thread: %s", str(e))

    t = threading.Thread(target=asjp_thread, daemon=True)
    t.start()

    flash("Scraping ASJP lance en arriere-plan !", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/setup-secret-univdz-2024")
def setup_db():
    from app.models.event import Revue
    from datetime import date
    try:
        db.create_all()
        if not Admin.query.filter_by(username="admin").first():
            admin = Admin(username="admin", email="admin@univdz.dz", is_superadmin=True)
            admin.set_password("UnivDZ2024!")
            db.session.add(admin)
        if Event.query.count() == 0:
            events = [
                Event(
                    titre="Colloque International sur l'Intelligence Artificielle",
                    type="colloque",
                    universite="USTHB",
                    discipline="Informatique",
                    wilaya="Alger",
                    date_debut=date(2025, 11, 15),
                    date_fin=date(2025, 11, 17),
                    date_limite=date(2025, 9, 30),
                    description="Un colloque reunissant des chercheurs autour des avancees en IA.",
                    lien_officiel="https://www.usthb.dz",
                    source="USTHB",
                    statut="valide",
                    score_fiabilite=0.9,
                    slug="colloque-ia-usthb-2025",
                ),
                Event(
                    titre="Bourse de Doctorat en Sciences Medicales",
                    type="bourse",
                    universite="Campus France Algerie",
                    discipline="Sciences medicales",
                    wilaya="Alger",
                    date_limite=date(2025, 7, 15),
                    description="Programme de bourses pour etudiants algeriens.",
                    lien_officiel="https://www.campusfrance.org",
                    source="Campus France",
                    statut="valide",
                    score_fiabilite=0.95,
                    slug="bourse-doctorat-medecine-2025",
                ),
                Event(
                    titre="Seminaire National sur les Energies Renouvelables",
                    type="seminaire",
                    universite="Universite de Bejaia",
                    discipline="Sciences de l'ingenieur",
                    wilaya="Bejaia",
                    date_debut=date(2025, 10, 5),
                    description="Seminaire sur les nouvelles technologies energetiques.",
                    lien_officiel="https://www.univ-bejaia.dz",
                    source="Universite Bejaia",
                    statut="valide",
                    score_fiabilite=0.85,
                    slug="seminaire-energies-renouvelables-bejaia-2025",
                ),
            ]
            for e in events:
                db.session.add(e)
        db.session.commit()
        return "<h1 style='color:green'>OK Base initialisee ! Admin: admin / UnivDZ2024! <a href='/admin'>Aller admin</a></h1>"
    except Exception as e:
        return "<h1 style='color:red'>Erreur: " + str(e) + "</h1>"