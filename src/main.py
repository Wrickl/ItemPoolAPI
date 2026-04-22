from logging.config import dictConfig

from fastapi import FastAPI

from .Util.logging.logger_config import log_config
from .controllers import TaskRegistration, TaskRetrieval, TaskCollection

dictConfig(log_config)

app = FastAPI()

app.include_router(TaskRegistration.router)
app.include_router(TaskRetrieval.router)
app.include_router(TaskCollection.router)
