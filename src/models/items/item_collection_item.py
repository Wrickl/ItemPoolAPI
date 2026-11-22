from uuid import UUID

from sqlmodel import Field, SQLModel


class ItemCollectionItem(SQLModel, table=True):
    __tablename__ = "ItemCollectionItem"

    item_collection_id: UUID = Field(
        foreign_key="ItemCollection.collection_id",
        primary_key=True,
    )
    item_id: UUID = Field(
        foreign_key="Item.item_id",
        primary_key=True,
    )
