from enum import Enum
import logging
import re
import subprocess
from typing import Any, Dict, List, NoReturn, Optional

from sentry_sdk import init
from sentry_sdk.types import Event, Hint

from managers.config import ConfigManager


class Debugs(Enum):
    WORLD_GENERATION = "world_generation"
    WORLD_SPAWNING = "world_spawning"

    SYSTEM_LOADING_CLASSES = "system_loading_classes"
    SYSTEM_LOADING_MODELS = "system_loading_models"
    SYSTEM_ASSET_GENERATION = "system_asset_generation"
    SYSTEM_AI = "system_ai"
    SYSTEM_SAVING = "system_saving"
    SYSTEM_LOADING = "system_loading"
    SYSTEM_ENTITY_GRAPH = "system_entity_graph"

    DISABLE_AI_TURN_PROCESSING = "disable_ai_turn_processing"


class Debug:
    CONFIG_BASE_KEY: str = "debug"
    CONFIG_DEBUGS_BASE_KEY: str = "debugs"

    _system_info: Optional[Dict[str, Any]] = None

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
        Debugs.DISABLE_AI_TURN_PROCESSING: config_instance_ref.get_by_key(
            (CONFIG_BASE_KEY, Debugs.DISABLE_AI_TURN_PROCESSING.value), default=False
        ),
        Debugs.SYSTEM_AI: config_instance_ref.get_by_key(
            (CONFIG_BASE_KEY, CONFIG_DEBUGS_BASE_KEY, Debugs.SYSTEM_AI.value), default=False
        ),
        Debugs.SYSTEM_SAVING: config_instance_ref.get_by_key(
            (CONFIG_BASE_KEY, CONFIG_DEBUGS_BASE_KEY, Debugs.SYSTEM_SAVING.value), default=False
        ),
        Debugs.SYSTEM_LOADING: config_instance_ref.get_by_key(
            (CONFIG_BASE_KEY, CONFIG_DEBUGS_BASE_KEY, Debugs.SYSTEM_LOADING.value), default=False
        ),
        Debugs.SYSTEM_ENTITY_GRAPH: config_instance_ref.get_by_key(
            (CONFIG_BASE_KEY, CONFIG_DEBUGS_BASE_KEY, Debugs.SYSTEM_ENTITY_GRAPH.value), default=False
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

    @classmethod
    def disable_ai_turn_processing(cls, override: Optional[bool] = None) -> bool:
        return cls._check_with_override(
            Debugs.DISABLE_AI_TURN_PROCESSING,
            override,
        )

    @classmethod
    def system_ai(cls, override: Optional[bool] = None) -> bool:
        return cls._check_with_override(
            Debugs.SYSTEM_AI,
            override,
        )

    @classmethod
    def system_saving(cls, override: Optional[bool] = None) -> bool:
        return cls._check_with_override(
            Debugs.SYSTEM_SAVING,
            override,
        )

    @classmethod
    def system_loading(cls, override: Optional[bool] = None) -> bool:
        return cls._check_with_override(
            Debugs.SYSTEM_LOADING,
            override,
        )

    @classmethod
    def system_entity_graph(cls, override: Optional[bool] = None) -> bool:
        return cls._check_with_override(
            Debugs.SYSTEM_ENTITY_GRAPH,
            override,
        )

    @classmethod
    def init_sentry(cls, dsn: str) -> init:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration
        from system.vars import __version__, get_git_commit, DEBUG

        # Set up Sentry logging integration
        sentry_logging = LoggingIntegration(
            level=logging.ERROR,  # Capture errors and above as breadcrumbs
            event_level=logging.ERROR,  # Send errors as events
        )

        sentry = sentry_sdk.init(
            dsn=dsn,
            release=f"Sciv@{__version__}",
            environment="development",
            traces_sample_rate=1.0,
            integrations=[sentry_logging],
            before_send=Debug.handle_crash,
        )

        sentry_sdk.set_tag("commit", get_git_commit())
        sentry_sdk.set_tag("debug", DEBUG)
        sentry_sdk.set_tag("version", __version__)
        sentry_sdk.set_context("config", ConfigManager.get_singleton_instance().get_config_full())

        return sentry

    @classmethod
    def handle_crash(cls, event: Event, hint: Hint) -> Optional[Event]:
        """
        This function is called by Sentry when an unhandled exception occurs.
        It gathers system data if debug mode is enabled and adds it to the event.
        """
        if cls._system_info is None:
            cls._system_info = cls.gether_system_data()

        if cls._system_info:
            event["extra"]["system_data"] = cls._system_info  # type: ignore[typeddict-item]

        return event

    @classmethod
    def gether_system_data(cls) -> Dict[str, Any]:
        """
        This function is only run if debug mode is enabled. and the user has enabled system data gathering.
        """

        from platform import uname
        from helpers.windows import WindowsHelper

        _uname = uname()

        data = {
            "system": _uname.system,
            "node": _uname.node,
            "release": _uname.release,
            "version": _uname.version,
            "machine": _uname.machine,
            "processor": _uname.processor,
        }

        if WindowsHelper.is_windows():
            data.update(cls._get_windows_info())
        else:
            data.update(cls._get_linux_info())

        return data

    @classmethod
    def _get_linux_info(cls) -> Dict[str, Any]:
        info: Dict[str, Any] = {"cpu": "", "ram_bytes": 0, "gpus": []}

        # CPU from /proc/cpuinfo
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("model name"):
                        info["cpu"] = line.split(":", 1)[1].strip()
                        break
        except Exception:
            pass

        # RAM from /proc/meminfo
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal"):
                        result = re.search(r"(\d+)", line)
                        if result:
                            kb = int(result.group(1))
                            info["ram_bytes"] = kb * 1024
                            break
                        continue
        except Exception:
            pass

        # GPUs via lspci
        try:
            out = subprocess.check_output(["lspci", "-nn"], text=True)
            gpus: List[str] = []
            for line in out.splitlines():
                if "VGA compatible controller" in line or "3D controller" in line:
                    # strip vendor-id tags
                    name = re.sub(r"\[.*?\]", "", line).split(":", 2)[-1].strip()
                    gpus.append(name)
            info["gpus"] = gpus
        except Exception:
            pass

        return info

    @classmethod
    def _get_windows_info(cls) -> Dict[str, Any]:
        info: Dict[str, Any] = {"cpu": "", "ram_bytes": 0, "gpus": []}

        # CPU
        try:
            out = subprocess.check_output(
                ["wmic", "cpu", "get", "Name", "/value"], text=True, stderr=subprocess.DEVNULL
            )
            matches = re.search(r"Name=(.+)", out)
            if matches:
                info["cpu"] = matches.group(1).strip()
        except Exception:
            pass

        # RAM
        try:
            out = subprocess.check_output(
                ["wmic", "ComputerSystem", "get", "TotalPhysicalMemory", "/value"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            matches = re.search(r"TotalPhysicalMemory=(\d+)", out)
            if matches:
                info["ram_bytes"] = int(matches.group(1))
        except Exception:
            pass

        # GPUs
        try:
            out = subprocess.check_output(
                ["wmic", "path", "win32_VideoController", "get", "Name"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            # skip header line
            lines = [line.strip() for line in out.splitlines() if line.strip()][1:]
            info["gpus"] = lines
        except Exception:
            pass

        return info
