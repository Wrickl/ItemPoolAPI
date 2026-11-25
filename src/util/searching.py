from collections.abc import Collection
from typing import Any
from uuid import UUID

from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import col, func, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from models import Creator, Item
from models.items.item_tag import ItemTag


def has_all_tags(names: Collection[str]) -> ColumnElement[bool]:
    unique_names = set(names)
    matching_items = (
        select(ItemTag.item_id)
        .where(col(ItemTag.name).in_(unique_names))
        .group_by(col(ItemTag.item_id))
        .having(func.count() == len(unique_names))
    )
    return col(Item.item_id).in_(matching_items)


def search_for_item(author_id: UUID | None, author_name: str | None) -> SelectOfScalar[Any]:
    stmt = select(Item)
    if author_id:
        stmt = stmt.where(Item.author_id == author_id)
    elif author_name:
        stmt = stmt.join(Creator).where(Creator.name.ilike(f"%{author_name}%"))
    return stmt
