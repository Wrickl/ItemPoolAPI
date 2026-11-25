from contextlib import asynccontextmanager
from logging.config import dictConfig
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from starlette.staticfiles import StaticFiles

from Util.logging.logger_config import log_config
from controllers import (
    item_collection,
    item_type_administration,
    plugin_administration,
    content_pieces_administration,
    solution_attempt,
    status_administration,
    item_administration,
    organisation_administration,
    themenbereich_administration,
    complex_type_administration,
    creator_administration,
    license_administration,
    content_section_administration,
    data_types_administration,
    ui_administration
)
from database.dao_connection import create_db_and_tables, get_engine
from database.mongo_connection import close_mongo_client
from services.PluginSystem import load_plugins
from services.data_type_registry import sync_database_types

dictConfig(log_config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_plugins()
    create_db_and_tables()
    with Session(get_engine()) as session:
        sync_database_types(session)
    yield
    close_mongo_client()


app = FastAPI(lifespan=lifespan)
##  Router für ENV Variablen
app.include_router(data_types_administration.router)
## Router für einfache Typen
app.include_router(status_administration.router)
app.include_router(organisation_administration.router)
app.include_router(license_administration.router)
app.include_router(themenbereich_administration.router)
app.include_router(creator_administration.router)

### Router für komplexe Typen
app.include_router(complex_type_administration.router)
app.include_router(item_type_administration.router)
app.include_router(content_pieces_administration.router)

app.include_router(content_section_administration.router)
### Router für Items
app.include_router(item_administration.router)
app.include_router(item_collection.router)

### Router für SolutionAttempts
app.include_router(solution_attempt.router)

### Router für Plugin-Administration
app.include_router(plugin_administration.router)

### Router für UI-Administration
app.include_router(ui_administration.router)

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

# Legacy redirects
