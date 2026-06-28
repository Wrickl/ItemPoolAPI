from uuid import UUID

from ...models.organisation import OrganisationBase


class OrganisationCreate(OrganisationBase):
    pass


class OrganisationRead(OrganisationBase):
    id: UUID
