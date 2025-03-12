from abc import ABC
from typing import Optional

from direct.showbase.DirectObject import DirectObject
from git import TYPE_CHECKING

from helpers.cache import Cache

if TYPE_CHECKING:
    from main import Openciv


class BaseEntity(ABC, DirectObject):
    def __init__(self):
        super().__init__()
        self.entity_key: Optional[str] = None
        self.entity_type_ref: Optional[str] = None
        self.is_registered: bool = False

        if Cache._instance is None:
            raise AssertionError("Cache instance is not set.")

        self.base: "Openciv" = Cache._instance

    def get_registered_status(self) -> bool:
        return self.is_registered
