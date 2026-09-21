from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlmodel import Session, select

from Util.database_functions import addmodell2database
from database import get_session
from models import Item
from models.Enums.Themenbereich import Themenbereich
from models.error import ResourceInUseException
from schemas.Tasks.Themenbereich import ThemenbereichResponse, ThemenbereichCreate, ThemenbereichUpdate

router = APIRouter()


@router.get("/getThemenbereich", response_model=list[ThemenbereichResponse], tags=["Themenbereich"])
async def get_themenbereich(session: Session = Depends(get_session)):
    """
    Rückgabe aller registrierten Themenbereiche.
    """
    return session.exec(select(Themenbereich)).all()


@router.get('/getThemenbereichById/{themenbereich_id}', response_model=ThemenbereichResponse, tags=["Themenbereich"])
def get_themenbereich_by_id(themenbereich_id: int, session: Session = Depends(get_session)):
    """
    Rückgabe eines Themenbereichs anhand der ID.
    """
    themenbereich = session.get(Themenbereich, themenbereich_id)
    if not themenbereich:
        raise HTTPException(status_code=404, detail="Themenbereich mit dieser ID nicht gefunden")
    return themenbereich


@router.post("/createThemenbereich", response_model=ThemenbereichResponse, tags=["Themenbereich"])
def create_themenbereich(themenbereich_data: ThemenbereichCreate, session: Session = Depends(get_session)):
    """
    Einen neuen Themenbereich anlegen.
    """
    themenbereich2add = Themenbereich.model_validate(themenbereich_data)
    addmodell2database("Themenbereich", themenbereich2add, session)
    return themenbereich2add


@router.put("/updateThemenbereich/{themenbereich_id}", response_model=ThemenbereichResponse, tags=["Themenbereich"])
def update_themenbereich(themenbereich_id: int, themenbereich_data: ThemenbereichUpdate,
                         session: Session = Depends(get_session)):
    """
    Einen bestehenden Themenbereich aktualisieren.
    """
    themenbereich2change = session.get(Themenbereich, themenbereich_id)
    if not themenbereich2change:
        raise HTTPException(status_code=404, detail=f"Themenbereich mit dieser ID {themenbereich_id} nicht gefunden")
    try:
        themenbereich2change.sqlmodel_update(themenbereich_data)
        session.commit()
        session.refresh(themenbereich2change)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=409, detail=f"Fehler beim Aktualisieren des Themenbereichs: {str(e)}")
    return themenbereich2change


@router.delete("/deleteThemenbereich/{themenbereich_id}", response_model=ThemenbereichResponse, tags=["Themenbereich"])
def delete_themenbereich(themenbereich_id: int, session: Session = Depends(get_session)):
    """
    Einen bestehenden Themenbereich löschen.
    """
    themenbereich2delete = session.get(Themenbereich, themenbereich_id)
    if not themenbereich2delete:
        raise HTTPException(status_code=404, detail=f"Themenbereich mit dieser ID {themenbereich_id} nicht gefunden")
    usage_count = session.scalar(select(func.count()).select_from(Item).where(Item.themenbereich == themenbereich_id))
    if usage_count:
        raise ResourceInUseException(usage_count)
    try:
        session.delete(themenbereich2delete)
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=409, detail=f"Fehler beim Löschen des Themenbereichs: {str(e)}")
    return themenbereich2delete
