from sqlalchemy import JSON, Column, String
from sqlmodel import Field, SQLModel


class QuestionTypeBase(SQLModel):
    name: str = Field(sa_column=Column(String(255), unique=True, nullable=False))
    description: str | None = Field(default=None)
    interaction_content_piece_ids: list[int] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    stimuli_content_piece_ids: list[int] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )


class QuestionType(QuestionTypeBase, table=True):
    __tablename__ = "QuestionType"

    question_type_id: int | None = Field(default=None, primary_key=True)
