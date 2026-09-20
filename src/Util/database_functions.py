from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session


def addmodell2database(model_name:str,model_data, database_session : Session):
    """
    Fügt ein Modell in die Datenbank ein.
    """
    try:
        database_session.add(model_data)
        database_session.commit()
        database_session.refresh(model_data)
    except IntegrityError:
        database_session.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"This {model_name} already exists.",
        )