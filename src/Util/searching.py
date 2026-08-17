from typing import Any

from sqlmodel import select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from ..models import Item, Creator


def search_for_item(author_id: str | None, author_name: str | None, database_id: int | None, q: str | None) -> \
        SelectOfScalar[Any]:
    stmt = select(Item)
    if q:
        stmt = stmt.where(Item.fragestellung.ilike(f"%{q}%"))
    if author_id:
        stmt = stmt.where(Item.author_id == author_id)
    elif author_name:
        stmt = stmt.join(Creator).where(Creator.name.ilike(f"%{author_name}%"))
    if database_id:
        stmt = stmt.where(Item.database_id == database_id)
    return stmt
