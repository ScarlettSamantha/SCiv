from typing import TYPE_CHECKING, Optional
from weakref import ReferenceType, ref
from gameplay.rules import get_game_rules
from managers.log import LogManager


if TYPE_CHECKING:
    from sciv.game import OpenCiv
    from system.atlas import AtlasGenerator
    from gameplay.rules import GameRules
    from sciv.managers.i18n import I18nManager


class Cache:
    _instance: Optional["OpenCiv"] = None
    _icon_atlas: Optional["AtlasGenerator"] = None
    _terrain_atlas: Optional["AtlasGenerator"] = None
    _active_rules: Optional["GameRules"] = get_game_rules()
    _core_logger: Optional[LogManager] = None
    _i18n_instance: Optional["I18nManager"] = None

    @classmethod
    def set_showbase_instance(cls, instance: "OpenCiv"):
        cls._instance = instance
        cls._logger = instance.logger

    @classmethod
    def get_showbase_instance(cls) -> "OpenCiv":
        assert cls._instance is not None, "Cache instance is not set."
        return cls._instance

    @classmethod
    def core_logger(cls) -> LogManager:
        if cls._core_logger is None:
            cls._core_logger = cls.get_showbase_instance().logger
        return cls._core_logger

    @classmethod
    def get_weakref(cls) -> ReferenceType["OpenCiv"]:
        assert cls._instance is not None, "Cache instance is not set."
        return ref(cls._instance)

    @classmethod
    def has_instance(cls) -> bool:
        return cls._instance is not None

    @classmethod
    def set_icon_atlas(cls, atlas: "AtlasGenerator"):
        assert atlas is not None, "Atlas instance cannot be not None."
        cls._icon_atlas = atlas

    @classmethod
    def get_icon_atlas(cls) -> "AtlasGenerator":
        if cls._icon_atlas is None:
            raise AssertionError("Atlas instance is not set.")
        return cls._icon_atlas

    @classmethod
    def set_terrain_atlas(cls, atlas: "AtlasGenerator"):
        assert atlas is not None, "Atlas instance cannot be not None."
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

    @classmethod
    def get_i18n_instance(cls) -> "I18nManager":
        if cls._i18n_instance is None:
            raise AssertionError("I18n instance is not set.")
        return cls._i18n_instance

    @classmethod
    def set_i18n_instance(cls, i18n: "I18nManager"):
        assert i18n is not None, "I18n instance cannot be not None."
        cls._i18n_instance = i18n
