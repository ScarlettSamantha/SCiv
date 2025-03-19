from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from main import SCIV


class Cache:
    _instance: Optional["SCIV"] = None

    @classmethod
    def set_showbase_instance(cls, instance: "SCIV"):
        cls._instance = instance

    @classmethod
    def get_showbase_instance(cls) -> "SCIV | None":
        return cls._instance
