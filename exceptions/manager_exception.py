from typing import Any
from exceptions._base_exception import BaseException


class ManagerException(BaseException):
    def __init__(self, *args: Any, **kwargs: Any):
        BaseException.__init__(self, *args, **kwargs)
