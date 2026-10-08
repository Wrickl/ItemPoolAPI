from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from Util.item_type import build_content_piece_read, build_full_content_piece_read
from database.dao_connection import get_session
from models import ContentPiece
from models.Tasks.content_types import (
    DataType,
)
from schemas.Tasks.ContentPiece import ContentPieceCreate, ContentPieceRead, ContentPieceReadFull

router = APIRouter(tags=["ContentPieces"])


@router.get("/getAllContentPieces", response_model=list[ContentPieceRead])
async def get_all_content_pieces(session: Session = Depends(get_session)):
    """Gibt alle verfuegbaren ContentPieces zurueck (fuer die UI-Auswahl)."""
    content_pieces = session.exec(select(ContentPiece).order_by(ContentPiece.name)).all()
    return [build_content_piece_read(cp) for cp in content_pieces]


@router.post("/createContentPiece", response_model=ContentPieceRead)
async def create_content_piece(content_piece_data: ContentPieceCreate, session: Session = Depends(get_session)):
    """Legt ein neues ContentPiece an."""
    data_type = session.get(DataType, content_piece_data.data_type_id)
    if data_type is None:
        raise HTTPException(
            status_code=404,
            detail=f"DataType {content_piece_data.data_type_id} nicht gefunden",
        )
    content_piece = ContentPiece.model_validate(content_piece_data)
    content_piece.validate_complex_type(session)  ## TODO Automatischer Abbgleich
    session.add(content_piece)
    session.commit()
    session.refresh(content_piece)
    return build_content_piece_read(content_piece)


@router.get("/getContentPieceById/{content_piece_id}")
async def get_content_piece_by_id(content_piece_id: UUID, show_complex_schema: bool, session: Session = Depends(get_session)):
    content_piece = session.get(ContentPiece, content_piece_id)
    if content_piece is None:
        raise HTTPException(
            status_code=404,
            detail=f"ContentPiece {content_piece_id} nicht gefunden",
        )
    if show_complex_schema:
        return ContentPieceReadFull.model_validate(build_full_content_piece_read(content_piece,session))
    else:
        return build_content_piece_read(content_piece)