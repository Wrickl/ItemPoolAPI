from typing import Literal

from pydantic import BaseModel


class Author(BaseModel):
    organisation: str
    person: str
    mail: str
    role: Literal["professor", "staff", "student"]
