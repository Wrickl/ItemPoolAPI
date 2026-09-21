from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from Util.database_functions import addmodell2database
from database import get_session
from models.Enums.Status import Status
from models.Tasks.tasks import Item
from models.error import ResourceInUseException
from schemas.Tasks.Status import StatusResponse, StatusCreate, StatusUpdate

router = APIRouter()


@router.get("/getAllStatus", response_model=list[StatusResponse], tags=["Status"])
async def get_status(session: Session = Depends(get_session)):
    """
    Rückgabe aller registrierten Status.
    """
    return session.exec(select(Status)).all()


@router.get('/getStatusById/{status_id}', response_model=StatusResponse, tags=["Status"])
def get_status_by_id(status_id: int, session: Session = Depends(get_session)):
    """
    Rückgabe eines Status anhand der ID.
    """
    status = session.get(Status, status_id)
    if not status:
        raise HTTPException(status_code=404, detail="Status mit dieser ID nicht gefunden")
    return status


@router.post("/createStatus", response_model=StatusResponse, tags=["Status"])
def create_status(status_data: StatusCreate, session: Session = Depends(get_session)):
    """
    Einen neuen Status anlegen.
    """
    status2add = Status.model_validate(status_data)
    addmodell2database("Status", status2add, session)
    return status2add


@router.put("/updateStatus/{status_id}", response_model=StatusResponse, tags=["Status"])
def update_status(status_id: int, status_data: StatusUpdate, session: Session = Depends(get_session)):
    """
    Einen bestehenden Status aktualisieren.
    """
    status2change = session.get(Status, status_id)
    if not status2change:
        raise HTTPException(status_code=404, detail=f"Status with this id {status_id} not found")
    try:
        status2change.sqlmodel_update(status_data)
        session.commit()
        session.refresh(status2change)
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail=f"This Status already exists.")
    return status2change


@router.delete("/deleteStatus/{status_id}", status_code=204, tags=["Status"])
def delete_status(status_id: int, session: Session = Depends(get_session)):
    """
    Einen bestehenden Status löschen.
    """
    status2delete = session.get(Status, status_id)
    if not status2delete:
        raise HTTPException(status_code=404, detail="Status not found")
    usage_count = session.scalar(select(func.count()).select_from(Item).where(Item.status == status_id))
    if usage_count:
        raise ResourceInUseException(usage_count)
    session.delete(status2delete)
    session.commit()
    return status2delete
