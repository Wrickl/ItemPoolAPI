from uuid import UUID

from ...models.Organisation import OrganisationBase


class OrganisationCreate(OrganisationBase):
    pass


class OrganisationRead(OrganisationBase):
    id: UUID
