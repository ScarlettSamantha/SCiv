from abc import ABC, abstractmethod
from typing import Any, Optional, Type, TypeVar

T = TypeVar("T", bound="Singleton")


class Singleton(ABC):
    __instance: Optional["Singleton"] = None

    @abstractmethod
    def __setup__(self, *args: Any, **kwargs: Any) -> None:
        """Method to set up the singleton instance."""
        pass

    def __new__(cls: Type[T], *args: Any, **kwargs: Any) -> T:
        if cls.__instance is None or not isinstance(cls.__instance, cls):
            instance = super(Singleton, cls).__new__(cls)  # type: ignore
            cls.__instance = instance
            instance.__setup__(*args, **kwargs)
        return cls.__instance

    @classmethod
    def get_singleton_instance(cls: Type[T], *args: Any, **kwargs: Any) -> T:
        if cls.__instance is None or not isinstance(cls.__instance, cls):
            cls.__instance = cls.__new__(cls, *args, **kwargs)
        return cls.__instance

    @classmethod
    def set_singleton_instance(cls: Type[T], instance: T) -> T:
        cls.__instance = instance
        return instance
