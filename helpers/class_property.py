from typing import Any, Type


class ClassProperty:
    def __init__(self, fget):
        self.fget = fget
        self.fset = None
        self.owner = None

    def __set_name__(self, owner: Type, name: str) -> None:
        self.owner = owner

    def __get__(self, instance, owner: Type) -> Any:
        return self.fget(owner)

    def __set__(self, instance, value: Any) -> None:
        if self.fset is None:
            raise AttributeError("can't set attribute")
        # Use stored owner from __set_name__
        return self.fset(self.owner, value)

    def setter(self, fset):
        self.fset = fset
        return self
