from abc import ABC

from ..database.dao import DAO


class Service(ABC):
    def __init__(self):
        self._dao: DAO = DAO
        pass
