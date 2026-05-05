from pydantic import BaseModel


class Organisation(BaseModel):
    name: str
    contact: str
    faculty: str
    ## Todo wird noch mehr benötigt?
