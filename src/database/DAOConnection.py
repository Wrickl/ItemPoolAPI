import os

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

from .. import models

load_dotenv()

# PostgreSQL-Verbindungskonfiguration aus Umgebungsvariablen
PG_USER = os.getenv("PG_USER") or os.getenv("POSTGRES_USER")
PG_PW = os.getenv("PG_PW") or os.getenv("POSTGRES_PASSWORD")
PG_DB = os.getenv("PG_DB") or os.getenv("POSTGRES_DB")
PG_PORT = os.getenv("PG_PORT") or os.getenv("POSTGRES_PORT") or "5432"
PG_HOST = os.getenv("PG_HOST") or os.getenv("POSTGRES_HOST") or "localhost"

if not all([PG_USER, PG_PW, PG_DB]):
    raise RuntimeError(
        "Postgres connection info missing. Set PG_USER/PG_PW/PG_DB (or POSTGRES_*)."
    )

# Datenbank-URL für SQLModel
database_url = f"postgresql+psycopg2://{PG_USER}:{PG_PW}@{PG_HOST}:{PG_PORT}/{PG_DB}"

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            database_url,
            echo=False,  # Setze auf True für SQL-Debugging
            future=True,
        )
    return _engine


def get_session():
    """
    FastAPI Dependency: liefert eine SQLModel Session für die Request.
    Wird nach dem Request automatisch geschlossen.
    """
    with Session(get_engine()) as session:
        yield session


def create_db_and_tables():
    """
    Erstelle alle Tabellen basierend auf den SQLModel-Definitionen.
    Optional - wird beim Start oder manuell aufgerufen.
    """
    SQLModel.metadata.create_all(get_engine())

