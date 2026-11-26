from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlmodel import Session, select

from util.database_functions import addmodell2database
from database import get_session
from models import Item
from models import Creator
from models import ResourceInUseException
from schemas.basic_metadata.author import CreatorCreate, CreatorResponse, CreatorUpdate

router = APIRouter()


@router.get("/getAllCreators", response_model=list[CreatorResponse], tags=["Creator"])
async def get_all_creators(session: Session = Depends(get_session)):
    """
    Alle Creator/Authors auslesen.
    """
    return session.exec(select(Creator)).all()


@router.get("/getCreatorById/{creator_id}", response_model=CreatorResponse, tags=["Creator"])
def get_creator_by_id(creator_id: UUID, session: Session = Depends(get_session)):
    """
    Rückgabe eines Creators anhand der ID.
    """
    creator = session.get(Creator, creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator nicht gefunden")
    return creator


@router.post("/createCreator", response_model=Creator, tags=["Creator"])
async def create_creator(creator_data: CreatorCreate, session: Session = Depends(get_session)):
    """
    Einen neuen Creator anlegen.
    """
    creator2add = Creator.model_validate(creator_data)
    ## C
    addmodell2database("Creator", creator2add, session)
    return creator2add


@router.put("/updateCreator/{creator_id}", response_model=CreatorResponse, tags=["Creator"])
def update_creator(
    creator_id: UUID,
    creator_data: CreatorUpdate,
    session: Session = Depends(get_session),
):
    """
    Update eines bestehenden Creators.
    """
    creator_to_update = session.get(Creator, creator_id)
    if creator_to_update is None:
        raise HTTPException(status_code=404, detail="Creator nicht gefunden")

    creator_to_update.sqlmodel_update(creator_data.model_dump())
    session.add(creator_to_update)
    session.commit()
    session.refresh(creator_to_update)
    return creator_to_update


@router.delete("/deleteCreator/{creator_id}", status_code=204, tags=["Creator"])
async def delete_creator(creator_id: UUID, session: Session = Depends(get_session)):
    """
    Einen Creator aus der Datenbank löschen.
    """
    creator2delete = session.get(Creator, creator_id)
    if not creator2delete:
        raise HTTPException(status_code=404, detail="Creator nicht gefunden")
    usage_count = session.scalar(
        select(func.count()).select_from(Item).where(Item.author_id == creator_id)
    )
    if usage_count:
        raise ResourceInUseException(usage_count)

    session.delete(creator2delete)
    session.commit()
