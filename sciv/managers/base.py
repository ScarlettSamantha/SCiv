from typing import Optional, TypeVar

TBaseManager = TypeVar("TBaseManager", bound="BaseManager")


class BaseManager:
    def __init__(self, parent: Optional["BaseManager"] = None):
        self._parent: Optional[BaseManager] = parent

    def getParent(self) -> Optional["BaseManager"]:
        return self._parent

    def setParent(self, parent: "BaseManager") -> None:
        self._parent = parent
