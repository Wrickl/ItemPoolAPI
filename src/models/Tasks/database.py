from typing import Optional, List
from typing import TYPE_CHECKING

from sqlalchemy import Column, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Relationship, Field

from ...schemas.Tasks.Database import DatabaseResponse
from ...schemas.contentblocks import ContentBlockAdapter

if TYPE_CHECKING:
    # avoid import-time circular dependency for type checking / linters
    from .tasks import Item


class DatabaseBase(SQLModel):
    ddl_string: Optional[str] = None
    version: Optional[str] = None
    dialect: Optional[str] = None
    weitere_eigenschaften: list[dict] = Field(
        default_factory=list,
        sa_column=Column(
            JSONB().with_variant(JSON(), "sqlite"),
            nullable=False,
        ),
    )


class Database(DatabaseBase, table=True):
    __tablename__ = "database"

    database_id: Optional[int] = Field(default=None, primary_key=True)
    items: List["Item"] = Relationship(back_populates="database")

    def to_read(self) -> DatabaseResponse:
        return DatabaseResponse(
            database_id=self.database_id,
            ddl_string=self.ddl_string,
            version=self.version,
            dialect=self.dialect,
            weitere_eigenschaften=[
                ContentBlockAdapter.validate_python(block)
                for block in self.weitere_eigenschaften
            ],
        )
