### TODO Vollstädnige CRUD Anwendung für Lizenzverwaltung implementieren
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlmodel import Session, select

from Util.database_functions import addmodell2database
from database import get_session
from models.Enums.License import License
from models.Tasks.tasks import Item
from models.error import ResourceInUseException
from schemas.Tasks.License import LicenseResponse, LicenseCreate

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
    addmodell2database("License", license2add, session)
    return license2add


@router.put("/updateLicense/{license_id}", response_model=LicenseResponse, tags=["Licence"])
async def update_license(license_id: int, license_data: LicenseCreate, session: Session = Depends(get_session)):
    """
    Eine bestehende Lizenz aktualisieren.
    """
    license2change = session.get(License, license_id)
    if not license2change:
        raise HTTPException(status_code=404, detail="License mit dieser ID nicht gefunden")
    try:
        license2change.sqlmodel_update(license_data)
        session.commit()
        session.refresh(license2change)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=409, detail=f"Fehler beim Aktualisieren der License: {str(e)}")
    return license2change


@router.delete("/deleteLicense/{license_id}", response_model=LicenseResponse, tags=["Licence"])
async def delete_license(license_id: int, session: Session = Depends(get_session)):
    """
    Eine bestehende Lizenz löschen.
    """
    license2delete = session.get(License, license_id)
    if not license2delete:
        raise HTTPException(status_code=404, detail="License mit dieser ID nicht gefunden")
    usage_count = session.scalar(select(func.count()).select_from(Item).where(Item.license == license_id))
    if usage_count:
        raise ResourceInUseException(usage_count)
    try:
        session.delete(license2delete)
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=409, detail=f"Fehler beim Löschen der License: {str(e)}")
    return license2delete
