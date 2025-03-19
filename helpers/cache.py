from typing import TYPE_CHECKING, Optional
from weakref import ReferenceType, ref

if TYPE_CHECKING:
    from main import SCIV


class Cache:
    _instance: Optional["SCIV"] = None

    @classmethod
    def set_showbase_instance(cls, instance: "SCIV"):
        cls._instance = instance

    @classmethod
    def get_showbase_instance(cls) -> "SCIV":
        if cls._instance is None:
            raise AssertionError("Cache instance is not set.")
        return cls._instance

    @classmethod
    def get_weakref(cls) -> ReferenceType["SCIV"]:
        if cls._instance is None:
            raise AssertionError("Cache instance is not set.")

        return ref(cls._instance)
