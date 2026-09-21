from uuid import UUID

from fastapi import Depends, APIRouter, HTTPException
from sqlmodel import Session, select

from Util.database_functions import addmodell2database
from database import get_session
from models.creator import Creator
from schemas.Author.Author import CreatorCreate, CreatorResponse

router = APIRouter()


@router.get("/getAllCreators", response_model=list[CreatorResponse], tags=["Creator"])
async def get_all_creators(session: Session = Depends(get_session)):
    """
    Alle Creator/Authors auslesen.
    """
    return session.exec(select(Creator)).all()
    # stmt = select(Creator, Organisation.name.label("organisation_name")).join(
    #     Organisation,
    #     Creator.organisation_id == Organisation.id,  # type: ignore[arg-type]
    # )
    # rows = session.exec(stmt).all()
    #
    # creators = []
    # for creator, organisation_name in rows:
    #     creators.append(
    #         CreatorRead(
    #             author_id=creator.author_id,
    #             email=creator.email,
    #             name=creator.name,
    #             role=creator.role,
    #             organisation_name=organisation_name,
    #         )
    #     )
    # return creators


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


@router.get("/updateCreator/{creator_id}", response_model=Creator, tags=["Creator"])
def update_organisation(creator_id: int, creator: Creator, session: Session = Depends(get_session)):
    """
    Update eines bestehenden Creators.
    """
    pass


@router.delete("/deleteCreator/{creator_id}", status_code=204, tags=["Creator"])
async def delete_creator(creator_id: int, session: Session = Depends(get_session)):
    """
    Einen Creator aus der Datenbank löschen.
    """
    creator2delete = session.get(Creator, creator_id)
    if not creator2delete:
        raise HTTPException(status_code=404, detail="Creator nicht gefunden")
    ## TODO Check if the creator is in use in item, if yes, raise 409
    session.delete(creator2delete)
    session.commit()
