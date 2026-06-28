import json

from Tasks import DatabaseCreate, Database

from ..models.Tasks import database


def create_database_from_schema(payload: DatabaseCreate) -> Database:
    return Database(
        ddl_string=payload.ddl_string,
        version=payload.version,
        dialect=payload.dialect,
        extended_description=[
            block.model_dump()
            for block in payload.weitere_eigenschaften
        ],
    )