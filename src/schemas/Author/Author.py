from uuid import UUID

from pydantic import ConfigDict

from ...models.Author import CreatorBase


class CreatorCreate(CreatorBase):
    pass


class CreatorRead(CreatorBase):
    author_id: UUID
    model_config = ConfigDict(from_attributes=True)
