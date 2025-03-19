from abc import ABC
from typing import TYPE_CHECKING, Optional

from direct.showbase.DirectObject import DirectObject

from helpers.cache import Cache

if TYPE_CHECKING:
    from main import SCIV


class BaseEntity(ABC, DirectObject):
    def __init__(self):
        super().__init__()
        self.entity_key: Optional[str] = None
        self.entity_type_ref: Optional[str] = None
        self.is_registered: bool = False

        if Cache._instance is None:
            raise AssertionError("Cache instance is not set.")

        self.base: "SCIV" = Cache._instance

    def get_registered_status(self) -> bool:
        return self.is_registered
