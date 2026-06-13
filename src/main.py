from logging.config import dictConfig
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pathlib import Path
from starlette.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from .controllers import TaskGeneration
from .controllers import SolutionAttempt
from .controllers import DatabaseGeneration
from .Util.logging.logger_config import log_config
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
app.include_router(DatabaseGeneration.router)

# Mount static UI files (Bootstrap-based frontend)
static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
	app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/ui", include_in_schema=False)
async def ui_root():
	"""Redirect to the static UI index page."""
	return RedirectResponse(url="/static/ui/index.html")


@app.get("/ui/create", include_in_schema=False)
async def ui_create():
	"""Redirect to the static item-create page."""
	return RedirectResponse(url="/static/ui/create.html")

#app.include_router(TaskRegistration.router)
#app.include_router(TaskRetrieval.router)
#app.include_router(TaskCollection.router)
