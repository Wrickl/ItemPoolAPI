from abc import ABC

from ..database.DAO import dao, DAO


class Service(ABC):
    def __init__(self):
        self._dao: DAO = dao
        pass
