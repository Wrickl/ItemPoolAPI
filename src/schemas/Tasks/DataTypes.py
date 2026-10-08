from pydantic import BaseModel, ConfigDict

### Data Type Create wird nicht benötigt, da nicht vom Benutzer erstellbar!

class DataTypeRead(BaseModel):
    data_type_id: int
    name: str
    description: str | None = None
    source: str

    model_config = ConfigDict(from_attributes=True)

class DataTypeResponse(BaseModel):
    data_type_id: int
    name: str
    description: str | None = None