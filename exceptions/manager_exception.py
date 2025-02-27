from __future__ import annotations
from exceptions._base_exception import BaseException


class ManagerException(BaseException):
    def __init__(self, *args, **kwargs):
        BaseException.__init__(self, *args, **kwargs)
