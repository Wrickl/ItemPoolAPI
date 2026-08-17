from fastapi import Depends, APIRouter
from sqlmodel import Session, select

from ..database.dao_connection import get_session
from ..models.Tasks.database import Database
from ..schemas.Tasks.Database import DatabaseResponse, DatabaseCreate

router = APIRouter()


@router.post("/createDatabase", response_model=DatabaseResponse, tags=["Databases"])
async def create_database(payload: DatabaseCreate, session: Session = Depends(get_session)):
    db_to_insert = Database(
        ddl_string=payload.ddl_string,
        version=payload.version,
        dialect=payload.dialect,
        weitere_eigenschaften=[
            block.model_dump()
            for block in payload.weitere_eigenschaften
        ],
    )
    session.add(db_to_insert)
    session.commit()
    session.refresh(db_to_insert)
    return db_to_insert


@router.get("/getAllDatabases", tags=["Databases"])
async def get_all_databases(session: Session = Depends(get_session)):
    databases = session.exec(select(Database)).all()
    return databases
