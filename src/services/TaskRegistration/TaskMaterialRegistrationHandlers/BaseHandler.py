from abc import ABC, abstractmethod

from archiv.models.TaskMaterials.BaseTaskMaterial import TaskMaterial
from archiv.models.Tasks.BaseTask import Metadata

from ....database.dao import DAO


class TaskMaterialHandler(ABC):
    def __init__(self, dao: DAO):
        self._dao = dao

    @abstractmethod
    def process_material(self, material: TaskMaterial) -> Metadata:
        """
        This method is exposed as a general interface to process any task material and should be implemented by the subsequent child-class.
        """
        return
