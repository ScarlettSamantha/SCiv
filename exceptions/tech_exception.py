from typing import Any
from exceptions.manager_exception import ManagerException


class TechException(ManagerException):
    def __init__(self, *args: Any, **kwargs: Any):
        ManagerException.__init__(self, *args, **kwargs)


class TechNotFoundException(TechException):
    def __init__(self, *args: Any, **kwargs: Any):
        TechException.__init__(self, *args, **kwargs)
