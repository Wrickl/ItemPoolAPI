from contextlib import asynccontextmanager
from logging.config import dictConfig
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from starlette.staticfiles import StaticFiles

from .Util.logging.logger_config import log_config
from .controllers import DatabaseGeneration
from .controllers import ItemCollection
from .controllers import PluginAdministration
from .controllers import SolutionAttempt
from .controllers import TaskGeneration
from .database.DAOConnection import create_db_and_tables
from .database.MongoConnection import close_mongo_client

dictConfig(log_config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield
    close_mongo_client()


app = FastAPI(lifespan=lifespan)
app.include_router(TaskGeneration.router)
app.include_router(SolutionAttempt.router)
app.include_router(ItemCollection.router)
app.include_router(DatabaseGeneration.router)
app.include_router(PluginAdministration.router)

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
