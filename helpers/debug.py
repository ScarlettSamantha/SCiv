from enum import Enum
from typing import Any, Dict, NoReturn, Optional

from managers.config import ConfigManager


class Debugs(Enum):
    WORLD_GENERATION = "world_generation"
    WORLD_SPAWNING = "world_spawning"

    SYSTEM_LOADING_CLASSES = "system_loading_classes"
    SYSTEM_LOADING_MODELS = "system_loading_models"
    SYSTEM_ASSET_GENERATION = "system_asset_generation"


class Debug:
    CONFIG_BASE_KEY: str = "debug"
    CONFIG_DEBUGS_BASE_KEY: str = "debugs"

    config_instance_ref = ConfigManager.get_singleton_instance()
    debug: bool = config_instance_ref.get_by_key((CONFIG_BASE_KEY, "enabled"), default=False)
    debug_modes: Dict[Debugs, bool] = {
        Debugs.WORLD_GENERATION: config_instance_ref.get_by_key(
            (CONFIG_BASE_KEY, CONFIG_DEBUGS_BASE_KEY, Debugs.WORLD_GENERATION.value), default=False
        ),
        Debugs.WORLD_SPAWNING: config_instance_ref.get_by_key(
            (CONFIG_BASE_KEY, CONFIG_DEBUGS_BASE_KEY, Debugs.WORLD_SPAWNING.value), default=False
        ),
        Debugs.SYSTEM_LOADING_CLASSES: config_instance_ref.get_by_key(
            (CONFIG_BASE_KEY, CONFIG_DEBUGS_BASE_KEY, Debugs.SYSTEM_LOADING_CLASSES.value), default=False
        ),
        Debugs.SYSTEM_LOADING_MODELS: config_instance_ref.get_by_key(
            (CONFIG_BASE_KEY, CONFIG_DEBUGS_BASE_KEY, Debugs.SYSTEM_LOADING_MODELS.value), default=False
        ),
        Debugs.SYSTEM_ASSET_GENERATION: config_instance_ref.get_by_key(
            (CONFIG_BASE_KEY, CONFIG_DEBUGS_BASE_KEY, Debugs.SYSTEM_ASSET_GENERATION.value), default=False
        ),
    }

    def __new__(cls, *args: Any, **kwargs: Any) -> NoReturn:
        raise TypeError(f"{cls.__name__} is not meant to be instantiated.")

    @classmethod
    def is_debug(cls) -> bool:
        return cls.debug

    @classmethod
    def _check_debug_mode(cls, mode: Debugs, default: Optional[bool] = None) -> bool:
        if mode not in cls.debug_modes:
            raise ValueError(f"Debug mode {mode} is not defined.")

        return cls.debug_modes[mode] if default is None else cls.debug_modes[mode] or default

    @classmethod
    def _check_with_override(cls, mode: Debugs, override: Optional[bool] = None) -> bool:
        return override if override is not None else cls._check_debug_mode(mode)

    @classmethod
    def world_generation(cls, override: Optional[bool] = None) -> bool:
        return cls._check_with_override(
            Debugs.WORLD_GENERATION,
            override,
        )

    @classmethod
    def world_spawning(cls, override: Optional[bool] = None) -> bool:
        return cls._check_with_override(
            Debugs.WORLD_SPAWNING,
            override,
        )

    @classmethod
    def system_loading_classes(cls, override: Optional[bool] = None) -> bool:
        return cls._check_with_override(
            Debugs.SYSTEM_LOADING_CLASSES,
            override,
        )

    @classmethod
    def system_loading_models(cls, override: Optional[bool] = None) -> bool:
        return cls._check_with_override(
            Debugs.SYSTEM_LOADING_MODELS,
            override,
        )

    @classmethod
    def system_asset_generation(cls, override: Optional[bool] = None) -> bool:
        return cls._check_with_override(
            Debugs.SYSTEM_ASSET_GENERATION,
            override,
        )
