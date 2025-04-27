from typing import TYPE_CHECKING, Optional
from weakref import ReferenceType, ref

if TYPE_CHECKING:
    from main import SCIV
    from system.atlas import AtlasGenerator


class Cache:
    _instance: Optional["SCIV"] = None
    _atlas: Optional["AtlasGenerator"] = None

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

    @classmethod
    def has_instance(cls) -> bool:
        return cls._instance is not None

    @classmethod
    def set_atlas(cls, atlas: "AtlasGenerator"):
        cls._atlas = atlas

    @classmethod
    def get_atlas(cls) -> "AtlasGenerator":
        if cls._atlas is None:
            raise AssertionError("Atlas instance is not set.")
        return cls._atlas
