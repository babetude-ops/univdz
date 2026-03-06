from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    universite = db.Column(db.String(300))
    discipline = db.Column(db.String(200))
    wilaya = db.Column(db.String(100))
    date_debut = db.Column(db.Date)
    date_fin = db.Column(db.Date)
    date_limite = db.Column(db.Date)
    description = db.Column(db.Text)
    lien_officiel = db.Column(db.String(1000))
    source = db.Column(db.String(500))
    date_collecte = db.Column(db.DateTime, default=datetime.utcnow)
    score_fiabilite = db.Column(db.Float, default=0.5)
    statut = db.Column(db.String(50), default="valide")
    date_validation = db.Column(db.DateTime)
    validated_by = db.Column(db.Integer, db.ForeignKey("admins.id"))
    slug = db.Column(db.String(600), unique=True)

    def __repr__(self):
        return f"<Event {self.titre[:50]}>"

    def to_dict(self):
        return {
            "id": self.id,
            "titre": self.titre,
            "type": self.type,
            "universite": self.universite,
            "discipline": self.discipline,
            "wilaya": self.wilaya,
            "date_debut": self.date_debut.isoformat() if self.date_debut else None,
            "date_fin": self.date_fin.isoformat() if self.date_fin else None,
            "date_limite": self.date_limite.isoformat() if self.date_limite else None,
            "description": self.description,
            "lien_officiel": self.lien_officiel,
            "source": self.source,
            "score_fiabilite": self.score_fiabilite,
            "statut": self.statut,
            "slug": self.slug,
        }


class Admin(UserMixin, db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_superadmin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    validated_events = db.relationship("Event", backref="validator", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Admin {self.username}>"


@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))
# ────────────────────────────────────────────────
#  Modèle Revue
# ────────────────────────────────────────────────
class Revue(db.Model):
    __tablename__ = "revues"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(500), nullable=False)
    domaine = db.Column(db.String(200))
    sous_domaine = db.Column(db.String(200))
    universite = db.Column(db.String(300))
    description = db.Column(db.Text)
    lien_officiel = db.Column(db.String(1000))
    lien_asjp = db.Column(db.String(1000))
    date_limite = db.Column(db.Date)
    annee_volume = db.Column(db.String(50))
    statut_appel = db.Column(db.String(100), default="ouvert")
    source = db.Column(db.String(500), default="ASJP")
    date_collecte = db.Column(db.DateTime, default=datetime.utcnow)
    score_fiabilite = db.Column(db.Float, default=0.8)
    statut = db.Column(db.String(50), default="a_verifier")
    slug = db.Column(db.String(600), unique=True)

    def __repr__(self):
        return f"<Revue {self.nom[:50]}>"

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "domaine": self.domaine,
            "sous_domaine": self.sous_domaine,
            "universite": self.universite,
            "lien_asjp": self.lien_asjp,
            "date_limite": self.date_limite.isoformat() if self.date_limite else None,
            "statut_appel": self.statut_appel,
            "slug": self.slug,
        }