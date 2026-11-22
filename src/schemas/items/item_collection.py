from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class ItemCollectionCreate(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=255, description="Anzeigename der Collection"
    )
    item_ids: list[int] = Field(..., min_length=1, description="Liste der Item-IDs")

    @model_validator(mode="after")
    def validate_unique_item_ids(self):
        if len(set(self.item_ids)) != len(self.item_ids):
            raise ValueError("`item_ids` darf keine Duplikate enthalten")
        return self


class ItemCollectionRead(BaseModel):
    collection_id: int
    name: str
    item_ids: list[int]
    created_at: datetime

    class Config:
        from_attributes = True
