from uuid import UUID

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import func
from sqlmodel import Session, select

from ..models.author import Creator
from ..Util.database_functions import addmodell2database
from ..schemas.Tasks.Organisation import OrganisationResponse,OrganisationCreate,OrganisationUpdate
from ..database import get_session
from ..models import Organisation
from ..models.error import ResourceInUseException

router = APIRouter()


@router.get("/getAllOrganisations",response_model=list[OrganisationResponse], tags=["Organisation"])
def get_all_organisations(session: Session = Depends(get_session)):
    """
    Rückgabe aller registrierten Organisationen
    """
    organisations = session.exec(select(Organisation)).all()
    return organisations

@router.get("/getOrganisation/{organisation_id}",response_model=OrganisationResponse, tags=["Organisation"])
def get_organisation(organisation_id: UUID, session: Session = Depends(get_session)):
    """
    Rückgabe einer Organisation anhand der ID
    """
    organisation = session.get(Organisation, organisation_id)
    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation nicht gefunden")
    return organisation

@router.post("/createOrganisation",response_model=OrganisationResponse, tags=["Organisation"])
def create_organisation(organisation_data: OrganisationCreate, session: Session = Depends(get_session)):
    ### TODO Organisation,benötigt ein Schema?
    """
    Eine neue Organisation anlegen.
    """
    organisation2add = Organisation.model_validate(organisation_data)
    addmodell2database("Organisation", organisation2add, session)
    return organisation2add


@router.put("/updateOrganisation/{organisation_id}",response_model=OrganisationResponse, tags=["Organisation"])
def update_organisation(organisation_id: UUID, organisation_data: OrganisationUpdate, session: Session = Depends(get_session)):
    """
    Eine bestehende Organisation aktualisieren.
    """
    organisation2change = session.get(Organisation, organisation_id)
    if not organisation2change:
        raise HTTPException(status_code=404, detail="Organisation nicht gefunden")
    try:
        organisation2change.sqlmodel_update(organisation_data)
        session.commit()
        session.refresh(organisation2change)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=409, detail=f"Fehler beim Aktualisieren der Organisation: {str(e)}")
    return organisation2change

@router.delete("/deleteOrganisation/{organisation_id}", status_code=204,tags=["Organisation"])
def delete_organisation(organisation_id: UUID, session: Session = Depends(get_session)):
    """
    Eine Organisation aus der Datenbank löschen.
    """

    organisation2delete = session.get(Organisation, organisation_id)
    if not organisation2delete:
        raise HTTPException(status_code=404, detail="Organisation nicht gefunden")
    usage_count= session.scalar(select(func.count()).select_from(Creator).where(Creator.organisation_id == organisation_id))
    if usage_count:
         raise ResourceInUseException(usage_count)
    session.delete(organisation2delete)
    session.commit()
    return organisation2delete