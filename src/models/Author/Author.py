from enum import Enum

from pydantic import BaseModel

from .Organisation import Organisation


class AuthorRole(str, Enum):
    professor = "professor" # Add/Edit/Delete Questions
    staff = "staff"
    student = "student"


class Author(BaseModel):
    name: str
    email: str
    organisation: Organisation
    role: AuthorRole
