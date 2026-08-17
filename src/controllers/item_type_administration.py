from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..database.dao_connection import get_session
from ..models.Tasks.content_types import ContentPiece, DataType, ItemType, ItemTypeContentPiece
from ..schemas.Tasks.content_types import (
    ContentPieceCreate,
    ContentPieceRead,
    DataTypeCreate,
    DataTypeRead,
    ItemTypeContentPieceAssign,
    ItemTypeContentPieceRead,
    ItemTypeCreate,
    ItemTypeDetailRead,
    ItemTypeRead,
)
from ..services.data_type_registry import sync_database_types

router = APIRouter()


def _build_content_piece_read(content_piece: ContentPiece) -> ContentPieceRead:
    if content_piece.content_piece_id is None:
        raise HTTPException(status_code=500, detail="ContentPiece ohne ID gefunden")
    return ContentPieceRead(
        content_piece_id=content_piece.content_piece_id,
        name=content_piece.name,
        description=content_piece.description,
        data_type_id=content_piece.data_type_id,
        data_type_name=content_piece.data_type.name if content_piece.data_type else None,
    )


def _build_data_type_read(data_type: DataType) -> DataTypeRead:
    if data_type.data_type_id is None:
        raise HTTPException(status_code=500, detail="DataType ohne ID gefunden")
    return DataTypeRead(
        data_type_id=data_type.data_type_id,
        name=data_type.name,
        description=data_type.description,
        source=data_type.source,
    )


def _build_item_type_assignment_read(assignment: ItemTypeContentPiece) -> ItemTypeContentPieceRead:
    if assignment.item_type_content_piece_id is None:
        raise HTTPException(status_code=500, detail="ItemTypeContentPiece ohne ID gefunden")
    if assignment.content_piece is None or assignment.content_piece.content_piece_id is None:
        raise HTTPException(status_code=500, detail="Zugehoeriges ContentPiece fehlt")
    if assignment.content_piece.data_type is None or assignment.content_piece.data_type.data_type_id is None:
        raise HTTPException(status_code=500, detail="Zugehoeriger DataType fehlt")

    return ItemTypeContentPieceRead(
        item_type_content_piece_id=assignment.item_type_content_piece_id,
        item_type_id=assignment.item_type_id,
        content_piece_id=assignment.content_piece.content_piece_id,
        position=assignment.position,
        is_required=assignment.is_required,
        content_piece_name=assignment.content_piece.name,
        content_piece_description=assignment.content_piece.description,
        data_type_id=assignment.content_piece.data_type.data_type_id,
        data_type_name=assignment.content_piece.data_type.name,
    )


def _build_item_type_detail(item_type: ItemType, session: Session) -> ItemTypeDetailRead:
    if item_type.item_type_id is None:
        raise HTTPException(status_code=500, detail="ItemType ohne ID gefunden")

    assignments = session.exec(
        select(ItemTypeContentPiece)
        .where(ItemTypeContentPiece.item_type_id == item_type.item_type_id)
        .order_by(ItemTypeContentPiece.position, ItemTypeContentPiece.item_type_content_piece_id)
    ).all()

    return ItemTypeDetailRead(
        item_type_id=item_type.item_type_id,
        name=item_type.name,
        description=item_type.description,
        content_pieces=[_build_item_type_assignment_read(assignment) for assignment in assignments],
    )


@router.get("/getAllDataTypes", response_model=list[DataTypeRead], tags=["ContentTypes"])
async def get_all_data_types(session: Session = Depends(get_session)):
    """Gibt alle verfuegbaren DataTypes zurueck."""
    data_types = session.exec(select(DataType).order_by(DataType.name)).all()
    return [_build_data_type_read(data_type) for data_type in data_types]


@router.post("/createDataType", response_model=DataTypeRead, tags=["ContentTypes"])
async def create_data_type(data_type_data: DataTypeCreate, session: Session = Depends(get_session)):
    """Legt einen neuen DataType fuer flexible ContentPieces an."""
    existing = session.exec(select(DataType).where(DataType.name == data_type_data.name)).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"DataType '{data_type_data.name}' existiert bereits")

    data_type = DataType.model_validate(data_type_data)
    session.add(data_type)
    session.commit()
    session.refresh(data_type)
    return _build_data_type_read(data_type)


@router.post("/syncAvailableDataTypes", response_model=list[DataTypeRead], tags=["ContentTypes"])
async def sync_available_data_types(session: Session = Depends(get_session)):
    """Synchronisiert DataTypes aus dem aktiven Datenbankdialekt."""
    synced_data_types = sync_database_types(session)
    return [_build_data_type_read(data_type) for data_type in synced_data_types]


@router.post("/createItemType", response_model=ItemTypeRead, tags=["ContentTypes"])
async def create_item_type(item_type_data: ItemTypeCreate, session: Session = Depends(get_session)):
    """Legt einen neuen ItemType an."""
    existing = session.exec(select(ItemType).where(ItemType.name == item_type_data.name)).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"ItemType '{item_type_data.name}' existiert bereits")

    item_type = ItemType.model_validate(item_type_data)
    session.add(item_type)
    session.commit()
    session.refresh(item_type)
    return ItemTypeRead.model_validate(item_type)


@router.get("/getAllItemTypes", response_model=list[ItemTypeDetailRead], tags=["ContentTypes"])
async def get_all_item_types(session: Session = Depends(get_session)):
    """Gibt alle ItemTypes inklusive zugewiesener ContentPieces zurueck."""
    item_types = session.exec(select(ItemType).order_by(ItemType.name)).all()
    return [_build_item_type_detail(item_type, session) for item_type in item_types]


@router.get("/getAllContentPieces", response_model=list[ContentPieceRead], tags=["ContentTypes"])
async def get_all_content_pieces(session: Session = Depends(get_session)):
    """Gibt alle verfuegbaren ContentPieces zurueck (fuer die UI-Auswahl)."""
    content_pieces = session.exec(select(ContentPiece).order_by(ContentPiece.name)).all()
    return [_build_content_piece_read(cp) for cp in content_pieces]


@router.post("/createContentPiece", response_model=ContentPieceRead, tags=["ContentTypes"])
async def create_content_piece(content_piece_data: ContentPieceCreate, session: Session = Depends(get_session)):
    """Legt ein neues ContentPiece an."""
    data_type = session.get(DataType, content_piece_data.data_type_id)
    if data_type is None:
        raise HTTPException(status_code=404, detail=f"DataType {content_piece_data.data_type_id} nicht gefunden")

    content_piece = ContentPiece.model_validate(content_piece_data)
    session.add(content_piece)
    session.commit()
    session.refresh(content_piece)
    return _build_content_piece_read(content_piece)


@router.post(
    "/assignContentPieceToItemType/{item_type_id}",
    response_model=ItemTypeDetailRead,
    tags=["ContentTypes"],
)
async def assign_content_piece_to_item_type(
        item_type_id: int,
        assignment_data: ItemTypeContentPieceAssign,
        session: Session = Depends(get_session),
):
    """Ordnet ein ContentPiece einem ItemType zu."""
    item_type = session.get(ItemType, item_type_id)
    if item_type is None:
        raise HTTPException(status_code=404, detail=f"ItemType {item_type_id} nicht gefunden")

    content_piece = session.get(ContentPiece, assignment_data.content_piece_id)
    if content_piece is None:
        raise HTTPException(status_code=404, detail=f"ContentPiece {assignment_data.content_piece_id} nicht gefunden")

    existing_assignment = session.exec(
        select(ItemTypeContentPiece).where(
            ItemTypeContentPiece.item_type_id == item_type_id,
            ItemTypeContentPiece.content_piece_id == assignment_data.content_piece_id,
        )
    ).first()
    if existing_assignment is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"ContentPiece {assignment_data.content_piece_id} ist ItemType {item_type_id} bereits zugeordnet"
            ),
        )

    assignment = ItemTypeContentPiece(
        item_type_id=item_type_id,
        content_piece_id=assignment_data.content_piece_id,
        position=assignment_data.position,
        is_required=assignment_data.is_required,
    )
    session.add(assignment)
    session.commit()

    return _build_item_type_detail(item_type, session)

