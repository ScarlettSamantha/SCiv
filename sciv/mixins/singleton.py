from __future__ import annotations

from threading import RLock
from typing import Any, Dict, Type, TypeVar, cast

T = TypeVar("T", bound="Singleton")


class Singleton:
    _instances: Dict[type, object] = {}
    _lock = RLock()

    def __new__(cls: Type[T], *args: Any, **kwargs: Any) -> T:
        with cls._lock:
            inst = cls._instances.get(cls)
            if inst is None:
                inst = super().__new__(cls)  # type: ignore[misc]
                cls._instances[cls] = inst
                setup = getattr(inst, "__setup__", None)
                if callable(setup):
                    setup(*args, **kwargs)  # type: ignore[misc]
            return cast(T, inst)

    @classmethod
    def instance(cls: Type[T], *args: Any, **kwargs: Any) -> T:
        return cls(*args, **kwargs)

    @classmethod
    def set_instance(cls: Type[T], instance: T) -> T:
        with cls._lock:
            cls._instances[cls] = instance
            return instance

    @classmethod
    def reset_instance(cls) -> None:
        with cls._lock:
            cls._instances.pop(cls, None)

    @classmethod
    def set_singleton_instance(cls: Type[T], instance: T) -> T:
        with cls._lock:
            cls._instances[cls] = instance
            return instance

    @classmethod
    def get_singleton_instance(cls: Type[T]) -> T:
        with cls._lock:
            inst = cls._instances.get(cls)
            return cast(T, inst)
