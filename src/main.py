from contextlib import asynccontextmanager
from logging.config import dictConfig
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from starlette.staticfiles import StaticFiles

from .Util.logging.logger_config import log_config
from .controllers import database_generation
from .controllers import item_collection
from .controllers import plugin_administration
from .controllers import solution_attempt
from .controllers import task_generation
from .database.dao_connection import create_db_and_tables
from .database.mongo_connection import close_mongo_client

dictConfig(log_config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield
    close_mongo_client()


app = FastAPI(lifespan=lifespan)
app.include_router(task_generation.router)
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
    return RedirectResponse(url='/ui')


@app.get("/ui", include_in_schema=False)
async def ui_root():
    """Redirect to the static UI index page."""
    return RedirectResponse(url="/static/ui/index.html")


@app.get("/ui/create", include_in_schema=False)
async def ui_create():
    """Redirect to the static item-create page."""
    return RedirectResponse(url="/static/ui/create.html")

# app.include_router(TaskRegistration.router)
# app.include_router(TaskRetrieval.router)
# app.include_router(TaskCollection.router)
