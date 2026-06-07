from typing import Optional, List

from pydantic import BaseModel, ConfigDict

from .BaseTaskMaterial import TaskMaterialRegistrationRequestObject, MaterialType
from .TextTaskMaterial import TextTaskMaterial


class InstructionalConstraint(BaseModel):
    model_config = ConfigDict(extra="allow")


class InstructionTaskMaterial(TextTaskMaterial):
    constraints: Optional[List[InstructionalConstraint]]


class TextMaterialRegistrationRequestObject(TaskMaterialRegistrationRequestObject):
    type: MaterialType.text
    material_information: InstructionTaskMaterial
