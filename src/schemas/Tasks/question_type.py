from pydantic import BaseModel, ConfigDict, Field


class QuestionTypeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    interaction_content_piece_ids: list[int] = Field(default_factory=list, min_length=1)
    stimuli_content_piece_ids: list[int] = Field(default_factory=list, min_length=1)


class QuestionTypeCreate(QuestionTypeBase):
    pass


class QuestionTypeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    interaction_content_piece_ids: list[int] | None = None
    stimuli_content_piece_ids: list[int] | None = None


class QuestionTypeInDBBase(QuestionTypeBase):
    question_type_id: int

    model_config = ConfigDict(from_attributes=True)


class QuestionTypeRead(QuestionTypeInDBBase):
    pass


class QuestionTypePublic(QuestionTypeInDBBase):
    pass
