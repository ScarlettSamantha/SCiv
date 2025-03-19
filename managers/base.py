from typing import Generic, Optional, TypeVar

TBaseManager = TypeVar("TBaseManager", bound="BaseManager")


class BaseManager(Generic[TBaseManager]):
    def __init__(self, parent: Optional[TBaseManager] = None):
        self._parent: Optional[TBaseManager] = parent

    def getParent(self) -> Optional[TBaseManager]:
        return self._parent

    def setParent(self, parent: TBaseManager) -> None:
        self._parent = parent
