from typing import Any

from sqlmodel import select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from ..models import Creator, Item


def search_for_item(
    author_id: str | None, author_name: str | None, q: str | None
) -> SelectOfScalar[Any]:
    stmt = select(Item)
    if author_id:
        stmt = stmt.where(Item.author_id == author_id)
    elif author_name:
        stmt = stmt.join(Creator).where(Creator.name.ilike(f"%{author_name}%"))
    return stmt
