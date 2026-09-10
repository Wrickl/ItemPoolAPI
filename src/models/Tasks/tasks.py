from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from sqlmodel import JSON, Column, Field, Relationship, SQLModel

from ..author import Creator

if TYPE_CHECKING:
    from src.models.Tasks.content_types import ItemContent, ItemType

class QuestionsBase(SQLModel):
    question_template: str
    description: str | None = Field(default=None, max_length=255)


class Questions(QuestionsBase, table=True):
    __tablename__ = "Questions"

    question_id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    placeholders: list["Placeholders"] = Relationship(back_populates="question")


# ===== Placeholders =====
class PlaceholdersBase(SQLModel):
    placeholder_order: int
    name: str = Field(max_length=100)
    data_type: str = Field(max_length=50)
    default_value: str | None = Field(default=None, max_length=255)
    fk_question_id: int = Field(foreign_key="Questions.question_id")


class Placeholders(PlaceholdersBase, table=True):
    __tablename__ = "Placeholders"

    placeholder_id: int | None = Field(default=None, primary_key=True)
    question: Questions = Relationship(back_populates="placeholders")


# ===== Item =====
class ItemBase(SQLModel):
    license: int | None = Field(default=None, foreign_key="license.license_id")
    status: int | None = Field(default=None, foreign_key="status.status_id")
    solution: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    themenbereich: int | None = Field(
        default=None, foreign_key="themenbereich.themenbereich_id"
    )
    interaction_content: list[dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(JSON)
    )
    stimuli_content: list[dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(JSON)
    )
    item_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    tags_id: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    author_id: UUID = Field(foreign_key="Author.author_id")
    item_type_id: int | None = Field(default=None, foreign_key="ItemType.item_type_id")


class Item(ItemBase, table=True):
    __tablename__ = "Item"

    item_id: int | None = Field(default=None, primary_key=True)
    author: Creator = Relationship(back_populates="items")
    item_type: Optional["ItemType"] = Relationship(back_populates="items")
    content_values: list["ItemContent"] = Relationship(back_populates="item")
