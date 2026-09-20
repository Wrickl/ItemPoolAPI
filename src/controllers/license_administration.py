### TODO Vollstädnige CRUD Anwendung für Lizenzverwaltung implementieren
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..database import get_session
from ..schemas.Tasks.License import LicenseResponse, LicenseCreate
from ..models.Enums.License import License

router = APIRouter()


@router.get("/getAllLicences", response_model=list[LicenseResponse], tags=["Licence"])
async def get_licence(session: Session = Depends(get_session)):
    """
    Rückgabe aller registrierten Lizenzen.
    """
    return session.exec(select(License)).all()

@router.get("/getLicenceById/{license_id}", response_model=LicenseResponse, tags=["Licence"])
async def get_licence(license_id: int, session: Session = Depends(get_session)):
    """
    Rückgabe einer registrierten Lizenz anhand der ID.
    """
    license = session.get(License, license_id)
    if not license:
        raise HTTPException(status_code=404, detail="License mit dieser ID nicht gefunden")
    return license


@router.post("/createLicense", response_model=LicenseResponse, tags=["Licence"])
async def create_license(
    license_data: LicenseCreate, session: Session = Depends(get_session)
):
    """
    Eine neue Lizenz anlegen.
    """
    license2add = License.model_validate(license_data)
    session.add(license2add)
    session.commit()
    session.refresh(license2add)
    return license2add

