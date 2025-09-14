from typing import Any, Callable, Optional, Self, Type


class ClassProperty:
    def __init__(self, fget: Callable[..., Any]):
        self.fget: Callable[..., Any] = fget
        self.fset: Optional[Callable[..., Any]] = None
        self.owner = None

    def __set_name__(self, owner: Type[Any], name: str) -> None:
        self.owner = owner

    def __get__(self, instance: Any, owner: Type[Any]) -> Any:
        return self.fget(owner)

    def __set__(self, instance: Any, value: Any) -> None:
        if self.fset is None:
            raise AttributeError("can't set attribute")
        return self.fset(self.owner, value)

    def setter(self, fset: Callable[..., Any]) -> Self:
        self.fset = fset
        return self
