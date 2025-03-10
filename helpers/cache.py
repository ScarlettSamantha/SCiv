from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from main import Openciv


class Cache:
    _instance: Optional["Openciv"] = None

    @classmethod
    def set_showbase_instance(cls, instance: "Openciv"):
        cls._instance = instance

    @classmethod
    def get_showbase_instance(cls) -> "Openciv | None":
        return cls._instance
