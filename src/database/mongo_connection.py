import os
from typing import Any

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

_mongo_client: Any | None = None


def _get_mongo_uri() -> str:
    mongo_uri = os.getenv("MONGO_URI")
    if mongo_uri:
        return mongo_uri

    host = os.getenv("MONGO_HOST", "localhost")
    port = os.getenv("MONGO_PORT", "27017")
    user = os.getenv("MONGO_USER")
    password = os.getenv("MONGO_PW")

    if user and password:
        return f"mongodb://{user}:{password}@{host}:{port}"
    return f"mongodb://{host}:{port}"


def get_mongo_client() -> Any:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(_get_mongo_uri())
    return _mongo_client


def get_mongo_database() -> Any:
    db_name = os.getenv("MONGO_DB", "itempool")
    return get_mongo_client()[db_name]


def get_solution_attempt_collection() -> Any:
    collection_name = os.getenv(
        "MONGO_SOLUTION_ATTEMPT_COLLECTION", "solution_attempts"
    )
    return get_mongo_database()[collection_name]


def get_solution_attempt_events_collection() -> Any:
    collection_name = os.getenv(
        "MONGO_SOLUTION_ATTEMPT_EVENTS_COLLECTION", "solution_attempt_events"
    )
    return get_mongo_database()[collection_name]


def get_solution_attempt_analyses_collection() -> Any:
    collection_name = os.getenv(
        "MONGO_SOLUTION_ATTEMPT_ANALYSES_COLLECTION", "solution_attempt_analyses"
    )
    return get_mongo_database()[collection_name]


def close_mongo_client() -> None:
    global _mongo_client
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None
