import click
import os
from app import create_app, db
from app.models.event import Admin, Event

app = create_app(os.environ.get("FLASK_ENV", "development"))


@app.cli.command("init-db")
def init_db():
    db.create_all()
    click.echo("✅ Base de données initialisée.")


@app.cli.command("create-admin")
@click.argument("username")
@click.argument("email")
@click.password_option()
def create_admin(username, email, password):
    with app.app_context():
        if Admin.query.filter_by(username=username).first():
            click.echo(f"❌ L'utilisateur '{username}' existe déjà.")
            return
        admin = Admin(username=username, email=email, is_superadmin=True)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        click.echo(f"✅ Administrateur '{username}' créé avec succès.")


@app.cli.command("scrape")
def scrape():
    from app.scrapers.runner import run_all_scrapers
    count = run_all_scrapers(app)
    click.echo(f"✅ {count} événement(s) collecté(s).")


@app.cli.command("seed")
def seed():
    from datetime import date
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
            description="Un colloque réunissant des chercheurs autour des avancées en IA.",
            lien_officiel="https://www.usthb.dz/colloque-ia-2025",
            source="USTHB",
            statut="valide",
            score_fiabilite=0.9,
            slug="colloque-international-ia-usthb-20251115",
        ),
        Event(
            titre="Bourse de Doctorat en Sciences Médicales",
            type="bourse",
            universite="Campus France Algérie",
            discipline="Sciences médicales",
            wilaya="Alger",
            date_limite=date(2025, 7, 15),
            description="Programme de bourses pour étudiants algériens.",
            lien_officiel="https://www.campusfrance.org/algerie",
            source="Campus France",
            statut="valide",
            score_fiabilite=0.95,
            slug="bourse-doctorat-medecine-campus-france-2025",
        ),
    ]
    for e in events:
        db.session.add(e)
    db.session.commit()
    click.echo(f"✅ {len(events)} événements de test insérés.")