# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from app.models.event import Admin, Event
from app import db
import threading, os, json

admin_bp = Blueprint("admin", __name__)

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), '../../site_settings.json')

DEFAULT_SETTINGS = {
    "site_nom": "DZcademia",
    "site_slogan": "Portail des opportunités académiques",
    "site_description": "Retrouvez tous les événements universitaires, bourses et revues scientifiques d'Algérie.",
    "menu_accueil": "Accueil",
    "menu_manifestations": "Manifestations scientifiques",
    "menu_bourses": "Bourses",
    "menu_revues": "Revues",
    "footer_texte": "DZcademia — Portail des opportunités académiques",
    "footer_copyright": "© 2026 DZcademia",
    "hero_titre": "événements universitaires recensés",
    "hero_texte": "",
    "hero_bouton": "Rechercher",
    "section_titre": "Dernières opportunités académiques",
    "couleur_primaire": "#1E3A5F",
    "couleur_secondaire": "#f5a623",
    "couleur_fond": "#F3F5F7",
    "couleur_surface": "#ffffff",
    "couleur_texte": "#1f2933",
    "couleur_succes": "#12b76a",
    "couleur_danger": "#f04438",
    "carte_fond": "#ffffff",
    "carte_bordure": "#e8f0fe",
    "carte_titre": "#1E3A5F",
    "carte_texte": "#6b7280",
    "carte_bouton": "#1E3A5F",
    "carte_bouton_texte": "#ffffff",
    "carte_ombre": "#1E3A5F",
    "section_fond": "#f8fafc",
    "section_titre_couleur": "#1E3A5F",
    "voir_tout_couleur": "#1E3A5F",
    "font_famille": "Inter",
    "font_size": "16",
    "font_size_titre": "36",
    "line_height": "1.6",
    "font_bold": "",
    "font_italic": "",
    "text_align": "left",
    "email_contact": "",
    # JSON string: {"pv-logo": {"anim": "pulse", "dur": "1s"}, ...}
    "element_animations": "",
    "element_animations_parsed": {},
    # JSON string: {"el-logo": {"left":30,"top":10,"width":200,"height":40,"z":10,"fontSize":20}, ...}
    "element_positions": "",
    "element_positions_parsed": {},
}


def get_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                merged = dict(DEFAULT_SETTINGS)
                merged.update(data)
                return merged
    except Exception:
        pass
    return dict(DEFAULT_SETTINGS)


def save_settings(form_data):
    try:
        current = get_settings()
        allowed = set(DEFAULT_SETTINGS.keys())

        for k, v in form_data.items():
            if k in allowed:
                current[k] = v

        # ── Parse animations JSON → dict ──────────────────────────
        raw_anim = current.get("element_animations", "")
        parsed_anim = {}
        if raw_anim:
            try:
                parsed_anim = json.loads(raw_anim)
            except (json.JSONDecodeError, TypeError):
                parsed_anim = {}
        current["element_animations_parsed"] = parsed_anim

        # ── Parse positions JSON → dict ───────────────────────────
        raw_pos = current.get("element_positions", "")
        parsed_pos = {}
        if raw_pos:
            try:
                parsed_pos = json.loads(raw_pos)
            except (json.JSONDecodeError, TypeError):
                parsed_pos = {}
        current["element_positions_parsed"] = parsed_pos

        with open(SETTINGS_FILE, 'w') as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        current_app.logger.error("Settings save error: %s", e)
        return False


# ─── Auth ────────────────────────────────────────────────────────────────────
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


# ─── Dashboard ───────────────────────────────────────────────────────────────
@admin_bp.route("/")
@login_required
def dashboard():
    stats = {
        "a_verifier": Event.query.filter_by(statut="a_verifier").count(),
        "valide":     Event.query.filter_by(statut="valide").count(),
        "rejete":     Event.query.filter_by(statut="rejete").count(),
    }
    recents = Event.query.filter_by(statut="a_verifier").order_by(Event.date_collecte.desc()).limit(10).all()
    return render_template("admin/dashboard.html", stats=stats, recents=recents)


# ─── File de validation ──────────────────────────────────────────────────────
@admin_bp.route("/queue")
@login_required
def queue():
    page   = request.args.get("page", 1, type=int)
    events = Event.query.filter_by(statut="a_verifier").order_by(Event.date_collecte.desc()).paginate(page=page, per_page=20)
    return render_template("admin/queue.html", events=events)


# ─── Tous les événements ─────────────────────────────────────────────────────
@admin_bp.route("/evenements")
@login_required
def tous_evenements():
    page          = request.args.get("page", 1, type=int)
    search        = request.args.get("search", "")
    statut_filter = request.args.get("statut", "")
    type_filter   = request.args.get("type", "")
    q = Event.query
    if search:        q = q.filter(Event.titre.ilike(f"%{search}%"))
    if statut_filter: q = q.filter_by(statut=statut_filter)
    if type_filter:   q = q.filter_by(type=type_filter)
    total      = q.count()
    pagination = q.order_by(Event.date_collecte.desc()).paginate(page=page, per_page=25)
    return render_template("admin/tous_evenements.html",
        events=pagination.items, pagination=pagination, total=total,
        search=search, statut_filter=statut_filter, type_filter=type_filter)


# ─── Créer un événement ──────────────────────────────────────────────────────
@admin_bp.route("/evenements/nouveau", methods=["GET", "POST"])
@login_required
def creer_evenement():
    if request.method == "POST":
        f = request.form
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                import uuid
                from werkzeug.utils import secure_filename
                ext      = secure_filename(file.filename).rsplit('.', 1)[-1].lower()
                filename = f"{uuid.uuid4().hex}.{ext}"
                upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_dir, exist_ok=True)
                file.save(os.path.join(upload_dir, filename))
                image_url = f"/static/uploads/{filename}"

        def parse_date(s):
            try: return datetime.strptime(s, "%Y-%m-%d").date() if s else None
            except: return None

        import re, unicodedata
        def slugify(s):
            s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode()
            return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

        event = Event(
            titre=f.get("titre"), type=f.get("type"),
            universite=f.get("universite"), discipline=f.get("discipline"),
            wilaya=f.get("wilaya"), description=f.get("description"),
            lien_officiel=f.get("lien_officiel"),
            date_debut=parse_date(f.get("date_debut")),
            date_fin=parse_date(f.get("date_fin")),
            date_limite=parse_date(f.get("date_limite")),
            statut=f.get("statut", "valide"), source=f.get("source", "Manuel"),
            score_fiabilite=1.0, slug=slugify(f.get("titre", ""))[:100], image=image_url,
        )
        db.session.add(event)
        db.session.commit()
        flash("✅ Événement créé avec succès !", "success")
        return redirect(url_for("admin.tous_evenements"))
    return render_template("admin/creer_evenement.html", event=None)


# ─── Modifier un événement ───────────────────────────────────────────────────
@admin_bp.route("/editer/<int:event_id>", methods=["GET", "POST"])
@login_required
def editer(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == "POST":
        f = request.form
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                import uuid
                from werkzeug.utils import secure_filename
                ext      = secure_filename(file.filename).rsplit('.', 1)[-1].lower()
                filename = f"{uuid.uuid4().hex}.{ext}"
                upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_dir, exist_ok=True)
                file.save(os.path.join(upload_dir, filename))
                event.image = f"/static/uploads/{filename}"

        def parse_date(s):
            try: return datetime.strptime(s, "%Y-%m-%d").date() if s else None
            except: return None

        event.titre       = f.get("titre", event.titre)
        event.type        = f.get("type", event.type)
        event.universite  = f.get("universite", event.universite)
        event.discipline  = f.get("discipline", event.discipline)
        event.wilaya      = f.get("wilaya", event.wilaya)
        event.description = f.get("description", event.description)
        event.lien_officiel = f.get("lien_officiel", event.lien_officiel)
        event.date_debut  = parse_date(f.get("date_debut")) or event.date_debut
        event.date_fin    = parse_date(f.get("date_fin"))   or event.date_fin
        event.date_limite = parse_date(f.get("date_limite")) or event.date_limite
        event.statut      = f.get("statut", event.statut)
        event.source      = f.get("source", event.source)
        db.session.commit()
        flash("✅ Événement modifié avec succès !", "success")
        return redirect(url_for("admin.tous_evenements"))
    return render_template("admin/creer_evenement.html", event=event)


# ─── Supprimer ───────────────────────────────────────────────────────────────
@admin_bp.route("/evenements/<int:event_id>/supprimer", methods=["POST"])
@login_required
def supprimer_evenement(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash("Événement supprimé.", "warning")
    return redirect(url_for("admin.tous_evenements"))


# ─── Valider / Rejeter ───────────────────────────────────────────────────────
@admin_bp.route("/valider/<int:event_id>", methods=["POST"])
@login_required
def valider(event_id):
    event = Event.query.get_or_404(event_id)
    event.statut = "valide"
    event.date_validation = datetime.utcnow()
    event.validated_by    = current_user.id
    db.session.commit()
    flash("Événement validé.", "success")
    return redirect(request.referrer or url_for("admin.queue"))


@admin_bp.route("/rejeter/<int:event_id>", methods=["POST"])
@login_required
def rejeter(event_id):
    event = Event.query.get_or_404(event_id)
    event.statut = "rejete"
    event.date_validation = datetime.utcnow()
    event.validated_by    = current_user.id
    db.session.commit()
    flash("Événement rejeté.", "warning")
    return redirect(request.referrer or url_for("admin.queue"))


# ─── Bourses ─────────────────────────────────────────────────────────────────
@admin_bp.route("/bourses")
@login_required
def toutes_bourses():
    try:
        from app.models.event import Bourse
        bourses = Bourse.query.order_by(Bourse.id.desc()).all()
    except Exception:
        bourses = Event.query.filter_by(type="bourse").order_by(Event.id.desc()).all()
    return render_template("admin/bourses.html", bourses=bourses)


# ─── Revues ──────────────────────────────────────────────────────────────────
@admin_bp.route("/revues")
@login_required
def toutes_revues():
    from app.models.event import Revue
    revues = Revue.query.order_by(Revue.id.desc()).all()
    return render_template("admin/revues.html", revues=revues)


@admin_bp.route("/revues/valider/<int:revue_id>", methods=["POST"])
@login_required
def valider_revue(revue_id):
    from app.models.event import Revue
    revue = Revue.query.get_or_404(revue_id)
    revue.statut = "valide"
    revue.date_validation = datetime.utcnow()
    revue.validated_by    = current_user.id
    db.session.commit()
    flash("Revue validée.", "success")
    return redirect(request.referrer or url_for("admin.toutes_revues"))


@admin_bp.route("/revues/rejeter/<int:revue_id>", methods=["POST"])
@login_required
def rejeter_revue(revue_id):
    from app.models.event import Revue
    revue = Revue.query.get_or_404(revue_id)
    revue.statut = "rejete"
    revue.date_validation = datetime.utcnow()
    revue.validated_by    = current_user.id
    db.session.commit()
    flash("Revue rejetée.", "warning")
    return redirect(request.referrer or url_for("admin.toutes_revues"))


# ─── Apparence ───────────────────────────────────────────────────────────────
@admin_bp.route("/apparence")
@login_required
def apparence():
    settings = get_settings()
    return render_template("admin/apparence.html", settings=settings)


@admin_bp.route("/apparence/sauver", methods=["POST"])
@login_required
def sauver_apparence():
    if save_settings(request.form.to_dict()):
        flash("✅ Apparence mise à jour et publiée !", "success")
    else:
        flash("❌ Erreur lors de la sauvegarde.", "danger")
    return redirect(url_for("admin.apparence"))


# ─── Scraper ─────────────────────────────────────────────────────────────────
@admin_bp.route("/scraper/lancer", methods=["POST"])
@login_required
def lancer_scraper():
    from app.scrapers.runner import run_all_scrapers
    app = current_app._get_current_object()
    def t():
        try: run_all_scrapers(app)
        except Exception as e: app.logger.error("[Scraper] %s", e)
    threading.Thread(target=t, daemon=True).start()
    flash("Scraping lancé en arrière-plan !", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/scraper/asjp", methods=["POST"])
@login_required
def lancer_scraper_asjp():
    from app.scrapers.asjp import ASJPScraper
    app = current_app._get_current_object()
    def t():
        try:
            scraper = ASJPScraper()
            scraper.run_revues(app)
        except Exception as e: app.logger.error("[ASJP] %s", e)
    threading.Thread(target=t, daemon=True).start()
    flash("Scraping ASJP lancé !", "success")
    return redirect(url_for("admin.dashboard"))


# ─── Setup ───────────────────────────────────────────────────────────────────
@admin_bp.route("/setup-secret-univdz-2024")
def setup_db():
    try:
        db.create_all()
        if not Admin.query.filter_by(username="admin").first():
            admin = Admin(username="admin", email="admin@univdz.dz", is_superadmin=True)
            admin.set_password("UnivDZ2024!")
            db.session.add(admin)
        db.session.commit()
        return "<h1 style='color:green'>OK ! <a href='/admin'>Aller admin</a></h1>"
    except Exception as e:
        return "<h1 style='color:red'>Erreur: " + str(e) + "</h1>"