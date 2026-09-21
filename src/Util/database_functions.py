import logging

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
    except IntegrityError as e:
        database_session.rollback()
        logging.warning(f"Conflict: IntegrityError {e.__traceback__} while adding {model_name} to the database.")
        raise HTTPException(
            status_code=409,
            detail=f"This {model_name} already exists.",
        )