from fastapi import Depends, APIRouter
from sqlmodel import Session, select

from Util.item_type import build_data_type_read, get_configured_upload_data_types
from database import get_session
from models import DataType
from schemas import DataTypeRead
from services.data_type_registry import sync_database_types

router = APIRouter()


@router.get("/getAllDataTypes", response_model=list[DataTypeRead], tags=["DataTypes"])
async def get_all_data_types(session: Session = Depends(get_session)):
    """Gibt alle verfuegbaren DataTypes zurueck."""
    data_types = session.exec(select(DataType).order_by(DataType.name)).all()
    return [build_data_type_read(data_type) for data_type in data_types]


@router.get("/getUploadDataTypes", response_model=list[str], tags=["DataTypes"])
async def get_upload_data_types() -> list[str]:
    """Gibt die Datentypen zurueck, die im Create-Form als File-Upload gerendert werden."""
    return get_configured_upload_data_types()


@router.get("/syncAvailableDataTypes", response_model=list[DataTypeRead], tags=["DataTypes"])
async def sync_available_data_types(session: Session = Depends(get_session)):
    """Synchronisiert DataTypes aus dem aktiven Datenbankdialekt."""
    synced_data_types = sync_database_types(session)
    return [build_data_type_read(data_type) for data_type in synced_data_types]
