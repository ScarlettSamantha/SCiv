from typing import Optional
from abc import ABC


class BaseEntity(ABC):
    def __init__(self):
        self.entity_key: Optional[str] = None
