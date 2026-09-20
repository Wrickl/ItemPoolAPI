from fastapi import Depends, APIRouter, HTTPException
from sqlmodel import Session, select

from ..schemas.Author.Author import CreatorRead, CreatorCreate
from ..database import get_session
from ..models.author import Creator
from ..models.organisation import Organisation

router = APIRouter()


@router.get("/getAllCreator", response_model=list[CreatorRead], tags=["Creator"])
async def get_all_creators(session: Session = Depends(get_session)):
    """
    Alle Creator/Authors aus der Datenbank auslesen.
    """
    stmt = select(Creator, Organisation.name.label("organisation_name")).join(
        Organisation,
        Creator.organisation_id == Organisation.id,  # type: ignore[arg-type]
    )
    rows = session.exec(stmt).all()

    creators = []
    for creator, organisation_name in rows:
        creators.append(
            CreatorRead(
                author_id=creator.author_id,
                email=creator.email,
                name=creator.name,
                role=creator.role,
                organisation_name=organisation_name,
            )
        )
    return creators


@router.post("/createCreator", response_model=Creator, tags=["Creator"])
async def create_creator(creator_data: CreatorCreate, session: Session = Depends(get_session)):
    """
    Einen neuen Creator anlegen.
    """
    creator2add = Creator.model_validate(creator_data)
    session.add(creator2add)
    session.commit()
    session.refresh(creator2add)
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
