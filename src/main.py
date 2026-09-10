from contextlib import asynccontextmanager
from logging.config import dictConfig
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from starlette.staticfiles import StaticFiles

from .controllers import (
    item_collection,
    item_type_administration,
    plugin_administration,
    solution_attempt,
    task_generation,
)
from .database.dao_connection import create_db_and_tables, get_engine
from .database.mongo_connection import close_mongo_client
from .services.data_type_registry import sync_database_types
from .Util.logging.logger_config import log_config

dictConfig(log_config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(get_engine()) as session:
        sync_database_types(session)
    yield
    close_mongo_client()


app = FastAPI(lifespan=lifespan)
app.include_router(task_generation.router)
app.include_router(item_type_administration.router)
app.include_router(solution_attempt.router)
app.include_router(item_collection.router)
app.include_router(database_generation.router)
app.include_router(plugin_administration.router)

# Mount static UI files (Bootstrap-based frontend)
static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url="/ui/dashboard")


@app.get("/ui", include_in_schema=False)
async def ui_root():
    """Redirect to the new dashboard."""
    return RedirectResponse(url="/ui/dashboard")


@app.get("/ui/dashboard", include_in_schema=False)
async def ui_dashboard():
    """Startseite mit Schnellzugriff und Übersicht."""
    return RedirectResponse(url="/static/ui/dashboard.html")


@app.get("/ui/items", include_in_schema=False)
async def ui_items():
    """Aufgaben durchsuchen und verwalten."""
    return RedirectResponse(url="/static/ui/index.html")


@app.get("/ui/new/items", include_in_schema=False)
async def ui_create():
    """Neue Aufgabe erstellen."""
    return RedirectResponse(url="/static/ui/create_form.html")

@app.get("/ui/new/solutionAttempts", include_in_schema=False)
async def ui_create_solution_attempt():
    """Neue Lösung versuchen."""
    return RedirectResponse(url="/static/ui/solution-attempt-create.html")


@app.get("/ui/items/new", include_in_schema=False)
async def ui_create_legacy_items_new():
    """Legacy redirect."""
    return RedirectResponse(url="/ui/new/items")


@app.get("/ui/items/{item_id}", include_in_schema=False)
async def ui_item_detail(item_id: str):
    """Detail-Ansicht einer Aufgabe."""
    return RedirectResponse(url="/static/ui/item-detail.html")


@app.get("/ui/items/{item_id}/attempts", include_in_schema=False)
async def ui_solution_attempt(item_id: str):
    """Lösungsversuch eingeben."""
    return RedirectResponse(url="/static/ui/solution-attempt.html")


@app.get("/ui/collections", include_in_schema=False)
async def ui_collections():
    """Sammlungen verwalten."""
    return RedirectResponse(url="/static/ui/collections.html")


@app.get("/ui/export", include_in_schema=False)
async def ui_export():
    """Export-Assistent."""
    return RedirectResponse(url="/static/ui/export.html")


@app.get("/ui/settings", include_in_schema=False)
async def ui_settings():
    """Einstellungen und Verwaltung."""
    return RedirectResponse(url="/static/ui/settings.html")


@app.get("/ui/settings/itemtypes", include_in_schema=False)
async def ui_settings_itemtypes():
    """Aufgabentypen verwalten."""
    return RedirectResponse(url="/static/ui/settings-itemtypes.html")


@app.get("/ui/settings/contenttypes", include_in_schema=False)
async def ui_settings_contenttypes():
    """Inhaltsbausteine verwalten."""
    return RedirectResponse(url="/static/ui/contenttypes.html")


@app.get("/ui/settings/creators", include_in_schema=False)
async def ui_settings_creators():
    """Autoren verwalten."""
    return RedirectResponse(url="/static/ui/settings-creators.html")


@app.get("/ui/settings/licenses", include_in_schema=False)
async def ui_settings_licenses():
    """Lizenzen verwalten."""
    return RedirectResponse(url="/static/ui/settings-licenses.html")


@app.get("/ui/settings/statuses", include_in_schema=False)
async def ui_settings_statuses():
    """Status verwalten."""
    return RedirectResponse(url="/static/ui/settings-statuses.html")


@app.get("/ui/settings/organizations", include_in_schema=False)
async def ui_settings_organizations():
    """Organisationen verwalten."""
    return RedirectResponse(url="/static/ui/organizations.html")


@app.get("/ui/settings/plugins", include_in_schema=False)
async def ui_settings_plugins():
    """Plugin-Verwaltung."""
    return RedirectResponse(url="/static/ui/settings-plugins.html")


# Legacy redirects
@app.get("/ui/create", include_in_schema=False)
async def ui_create_legacy():
    return RedirectResponse(url="/ui/new/items")


@app.get("/ui/create_form", include_in_schema=False)
async def ui_create_form_legacy():
    return RedirectResponse(url="/static/ui/create_form.html")
