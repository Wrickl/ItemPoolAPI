from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from ..database import get_session
from ..models.Tasks.tasks import Item
from ..models.complextype import ComplexType
from ..models.error import ResourceInUseException
from ..schemas.complextype import ComplexTypeResponse, ComplexTypeCreate

router = APIRouter()


@router.get("/getAllComplexType", response_model=list[ComplexTypeResponse], tags=["ComplexType"])
async def get_complex_types(session: Session = Depends(get_session)):
    """
    Rückgabe aller registrierten komplexen Typen.
    """
    return session.exec(select(ComplexType)).all()


@router.get('/getComplexTypeById/{complex_type_id}', response_model=ComplexTypeResponse, tags=["ComplexType"])
async def get_complex_type_by_id(complex_type_id: int, session: Session = Depends(get_session)):
    """
    Rückgabe eines komplexen Typs anhand der ID.
    """
    complex_type = session.get(ComplexType, complex_type_id)
    if not complex_type:
        raise HTTPException(status_code=404, detail="Komplexer Typ mit dieser ID nicht gefunden")
    return complex_type


@router.post("/createComplexType", response_model=ComplexTypeResponse, tags=["ComplexType"])
async def create_complex_type(complex_type_data: ComplexTypeCreate, session: Session = Depends(get_session)):
    """
    Einen neuen Status anlegen.
    """
    complex_type2add = ComplexType(name=complex_type_data.name, description=complex_type_data.description,
                                   json_schema=complex_type_data.json_schema)
    try:
        session.add(complex_type2add)
        session.commit()
        session.refresh(complex_type2add)
        return complex_type2add

    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ein komplexer Typ mit diesem Namen existiert bereits.",
        )


@router.put("/updateComplexType/{complex_type_id}", response_model=ComplexTypeResponse, tags=["ComplexType"])
async def update_complex_type(complex_type_id: int, complex_type_data: ComplexTypeCreate,
                              session: Session = Depends(get_session)):
    """
    Einen bestehenden komplexen Typ aktualisieren.
    """
    complex_type2change = session.get(ComplexType, complex_type_id)
    if not complex_type2change:
        raise HTTPException(status_code=404, detail=f"Komplexer Typ mit dieser ID {complex_type_id} nicht gefunden")
    (complex_type2change.name, complex_type2change.description,
     complex_type2change.json_schema) = (complex_type_data.name, complex_type_data.description,
                                         complex_type_data.json_schema)
    session.add(complex_type2change)
    session.commit()
    session.refresh(complex_type2change)
    return complex_type2change


@router.delete("/deleteComplexType/{complex_type_id}", status_code=204, tags=["ComplexType"])
async def delete_complex_type(complex_type_id: int, session: Session = Depends(get_session)):
    """
    Einen bestehenden Status löschen.
    """
    complex_type2delete = session.get(ComplexType, complex_type_id)
    if not complex_type2delete:
        raise HTTPException(status_code=404, detail="Complex Type not found")
    # TODO einfügen wenn klar wo Complex Type eingesetzen werden. Frage wie kommt man an diese Information.??
    # usage_count = session.scalar(select(func.count()).select_from(Status).where(Item.status == status_id))
    # if usage_count:
    #     raise ResourceInUseException(usage_count)
    session.delete(complex_type2delete)
    session.commit()
    return complex_type2delete
