from typing import TYPE_CHECKING, Optional
from weakref import ReferenceType, ref
from gameplay.rules import get_game_rules

if TYPE_CHECKING:
    from main import SCIV
    from system.atlas import AtlasGenerator
    from gameplay.rules import GameRules


class Cache:
    _instance: Optional["SCIV"] = None
    _icon_atlas: Optional["AtlasGenerator"] = None
    _terrain_atlas: Optional["AtlasGenerator"] = None
    _active_rules: Optional["GameRules"] = get_game_rules()

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
    def set_icon_atlas(cls, atlas: "AtlasGenerator"):
        cls._icon_atlas = atlas

    @classmethod
    def get_icon_atlas(cls) -> "AtlasGenerator":
        if cls._icon_atlas is None:
            raise AssertionError("Atlas instance is not set.")
        return cls._icon_atlas

    @classmethod
    def set_terrain_atlas(cls, atlas: "AtlasGenerator"):
        cls._terrain_atlas = atlas

    @classmethod
    def get_terrain_atlas(cls) -> "AtlasGenerator":
        if cls._terrain_atlas is None:
            raise AssertionError("Atlas instance is not set.")
        return cls._terrain_atlas

    @classmethod
    def get_active_rules(cls) -> "GameRules":
        if cls._active_rules is None:
            raise AssertionError("Active game rules are not set.")
        return cls._active_rules

    @classmethod
    def set_active_rules(cls, rules: "GameRules"):
        cls._active_rules = rules
