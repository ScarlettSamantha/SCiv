from typing import Optional
from abc import ABC


class BaseEntity(ABC):
    def __init__(self):
        self.entity_key: Optional[str] = None
        self.entity_type_ref: Optional[str] = None
        self.is_registered: bool = False

    def get_registered_status(self) -> bool:
        return self.is_registered
