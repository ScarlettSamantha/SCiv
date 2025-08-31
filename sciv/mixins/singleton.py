from threading import RLock
from typing import Any, Dict, List, Type, TypeVar, cast

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
    def get_singleton_instance(cls: Type[T], *, allow_subclass_fallback: bool = False) -> T:
        with cls._lock:
            inst = cls._instances.get(cls)
            if inst is not None:
                return cast(T, inst)

            if allow_subclass_fallback:
                for instance_cls, inst in cls._instances.items():
                    try:
                        if issubclass(instance_cls, cls):
                            return cast(T, inst)
                    except TypeError:
                        continue
            raise ValueError(f"No instance of singleton class {cls.__name__} has been set.")

    @classmethod
    def debug_list_instances(cls) -> List[Dict[str, Any]]:
        with cls._lock:
            out: List[Any] = []
            for k, v in cls._instances.items():
                out.append(
                    {
                        "key_id": id(k),
                        "key_repr": repr(k),
                        "module": getattr(k, "__module__", None),
                        "qualname": getattr(k, "__qualname__", None),
                        "instance_id": id(v),
                    }
                )
            return out
