from datetime import datetime, timezone
from typing import Any, Optional, List, TYPE_CHECKING
from uuid import UUID

from sqlmodel import SQLModel, Field, Relationship, Column, JSON

from .database import Database
from ..Enums.Questiontypes import QuestionTypes
from ..author import Creator

if TYPE_CHECKING:
    from src.models.Tasks.content_types import ItemType, ItemContent

"""TODO Metaschicht einziehen alle Hardcodiert Sachen entfernen"""


# ===== Questions =====
class QuestionsBase(SQLModel):
    question_template: str
    description: Optional[str] = Field(default=None, max_length=255)


class Questions(QuestionsBase, table=True):
    __tablename__ = "Questions"

    question_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    placeholders: List["Placeholders"] = Relationship(back_populates="question")


# ===== Placeholders =====
class PlaceholdersBase(SQLModel):
    placeholder_order: int
    name: str = Field(max_length=100)
    data_type: str = Field(max_length=50)
    default_value: Optional[str] = Field(default=None, max_length=255)
    fk_question_id: int = Field(foreign_key="Questions.question_id")


class Placeholders(PlaceholdersBase, table=True):
    __tablename__ = "Placeholders"

    placeholder_id: Optional[int] = Field(default=None, primary_key=True)
    question: Questions = Relationship(back_populates="placeholders")


# ===== Item =====
class ItemBase(SQLModel):
    license: Optional[int] = Field(default=None, foreign_key="license.license_id")
    status: Optional[int] = Field(default=None, foreign_key="status.status_id")
    fragestellung: Optional[str] = None
    solution: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    fragenart: Optional[int] = Field(default=None, foreign_key="themenbereich.themenbereich_id")
    question_type: Optional[QuestionTypes] = None  ## TODO entferne und durch ContentType Picese ersetzen
    interaction_content: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    stimuli_content: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    item_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    tags_id: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    author_id: UUID = Field(foreign_key="Author.author_id")
    database_id: Optional[int] = Field(default=None, foreign_key="database.database_id")
    item_type_id: Optional[int] = Field(default=None, foreign_key="ItemType.item_type_id")


class Item(ItemBase, table=True):
    __tablename__ = "Item"

    item_id: Optional[int] = Field(default=None, primary_key=True)
    author: Creator = Relationship(back_populates="items")
    database: Optional[Database] = Relationship(back_populates="items")
    item_type: Optional["ItemType"] = Relationship(back_populates="items")
    content_values: List["ItemContent"] = Relationship(back_populates="item")
