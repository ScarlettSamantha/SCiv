import gzip
import io
import logging
import re
import subprocess  # nosec: B404
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Mapping, NoReturn, Optional, Tuple

import orjson as json
from direct.task.Task import Task
from helpers.cache import Cache
from helpers.paths import PathsHelper
from managers.config import ConfigManager
from panda3d.core import ClockObject, PythonTask

if TYPE_CHECKING:
    from gameplay.tile import Tile
    from sentry_sdk import init
    from sentry_sdk.types import Event, Hint
    from system.generators.base import BaseGenerator


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
    SYSTEM_PERFORMANCE_LOGGING = "system_performance_logging"
    SYSTEM_INPUT = "system_input"
    SYSTEM_UNITS = "system_units"

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
        Debugs.SYSTEM_PERFORMANCE_LOGGING: config_instance_ref.get_by_key(
            (CONFIG_BASE_KEY, CONFIG_DEBUGS_BASE_KEY, Debugs.SYSTEM_PERFORMANCE_LOGGING.value), default=False
        ),
        Debugs.SYSTEM_INPUT: config_instance_ref.get_by_key(
            (CONFIG_BASE_KEY, CONFIG_DEBUGS_BASE_KEY, Debugs.SYSTEM_INPUT.value), default=False
        ),
        Debugs.SYSTEM_UNITS: config_instance_ref.get_by_key(
            (CONFIG_BASE_KEY, CONFIG_DEBUGS_BASE_KEY, Debugs.SYSTEM_UNITS.value), default=False
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
    def system_performance_logging(cls, override: Optional[bool] = None) -> bool:
        return cls._check_with_override(
            Debugs.SYSTEM_PERFORMANCE_LOGGING,
            override,
        )

    @classmethod
    def system_input(cls, override: Optional[bool] = None) -> bool:
        return cls._check_with_override(
            Debugs.SYSTEM_INPUT,
            override,
        )

    @classmethod
    def system_units(cls, override: Optional[bool] = None) -> bool:
        return cls._check_with_override(
            Debugs.SYSTEM_UNITS,
            override,
        )

    @classmethod
    def init_sentry(cls, dsn: str) -> "init":
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration
        from system.vars import DEBUG, __version__, get_git_commit

        sentry_logging = LoggingIntegration(
            level=logging.ERROR,
            event_level=logging.ERROR,
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
    def handle_crash(cls, event: "Event", hint: "Hint") -> Optional["Event"]:
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

        from helpers.os import WindowsHelper

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
        except Exception:  # nosec: B110
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
        except Exception:  # nosec: B110
            pass

        # GPUs via lspci
        try:
            out = subprocess.check_output(["lspci", "-nn"], text=True)  # nosec: B603, B607
            gpus: List[str] = []
            for line in out.splitlines():
                if "VGA compatible controller" in line or "3D controller" in line:
                    # strip vendor-id tags
                    name = re.sub(r"\[.*?\]", "", line).split(":", 2)[-1].strip()
                    gpus.append(name)
            info["gpus"] = gpus
        except Exception:  # nosec: B110
            pass

        return info

    @classmethod
    def _get_windows_info(cls) -> Dict[str, Any]:
        info: Dict[str, Any] = {"cpu": "", "ram_bytes": 0, "gpus": []}

        # CPU
        try:
            out = subprocess.check_output(  # nosec: B603, B607
                ["wmic", "cpu", "get", "Name", "/value"], text=True, stderr=subprocess.DEVNULL
            )
            matches = re.search(r"Name=(.+)", out)
            if matches:
                info["cpu"] = matches.group(1).strip()
        except Exception:  # nosec: B110
            pass

        # RAM
        try:
            out = subprocess.check_output(  # nosec: B603, B607
                ["wmic", "ComputerSystem", "get", "TotalPhysicalMemory", "/value"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            matches = re.search(r"TotalPhysicalMemory=(\d+)", out)
            if matches:
                info["ram_bytes"] = int(matches.group(1))
        except Exception:  # nosec: B110
            pass

        # GPUs
        try:
            out = subprocess.check_output(  # nosec: B603, B607
                ["wmic", "path", "win32_VideoController", "get", "Name"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            # skip header line
            lines = [line.strip() for line in out.splitlines() if line.strip()][1:]
            info["gpus"] = lines
        except Exception:  # nosec: B110
            pass

        return info

    @classmethod
    def get_python_version(cls) -> str:
        import sys

        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} ({sys.platform})"

    @classmethod
    def get_git_commit(cls) -> str:
        from system.vars import get_git_commit

        return get_git_commit()

    @classmethod
    def get_git_branch(cls) -> str:
        from system.vars import get_git_branch

        return get_git_branch()

    @classmethod
    def get_config_path(cls) -> str:
        config = ConfigManager.get_singleton_instance()
        return config.config_file

    @classmethod
    def open_config_folder(cls) -> None:
        config = ConfigManager.get_singleton_instance()
        config_path = config.config_file

        if not config_path:
            logging.warning("No config file found.")
            return

        try:
            PathsHelper.open_folder(str(Path(config_path).parent))
        except Exception as e:
            logging.error(f"Failed to open config folder: {e}")

    @classmethod
    def open_data_folder(cls) -> None:
        data_dir = PathsHelper.get_data_dir()

        if not data_dir:
            logging.warning("No data directory found.")
            return

        try:
            PathsHelper.open_folder(data_dir)
        except Exception as e:
            logging.error(f"Failed to open data folder: {e}")

    @classmethod
    def get_panda_version(cls) -> str:
        try:
            import panda3d

            return panda3d.__version__  #  type: ignore
        except ImportError:
            return "Panda3D not installed"
        except Exception as e:
            return f"Error getting Panda3D version: {e}"

    @classmethod
    def get_kivy_version(cls) -> str:
        try:
            import kivy  # type: ignore[import]

            return kivy.__version__  #  type: ignore
        except ImportError:
            return "Kivy not installed"
        except Exception as e:
            return f"Error getting Kivy version: {e}"

    @classmethod
    def trigger_sentry_dump(
        cls,
        message: str = "User-triggered debug dump",
        *,
        level: Literal["debug", "info", "warning", "error", "fatal"] = "info",
        jpeg_quality: int = 85,
        tags: Optional[Mapping[str, str]] = None,
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Optional[str]:
        try:
            import sentry_sdk  # type: ignore[import]
        except Exception:
            logging.warning("Sentry SDK not installed; cannot send dump.")
            return None

        hub = sentry_sdk.Hub.current
        if not hub or not hub.client:
            logging.warning("Sentry is not initialized; cannot send dump.")
            return None

        try:
            base = Cache.get_showbase_instance()
            win = getattr(base, "win", None)
            if win is None:
                logging.warning("No active Panda3D window; cannot capture screenshot.")
                return None

            from panda3d.core import PNMImage, StringStream  # type: ignore[import]

            img = PNMImage()
            if not win.getScreenshot(img):
                logging.error("getScreenshot() failed.")
                return None

            jpeg_bytes: bytes
            try:
                import io as _io

                from PIL import Image  # type: ignore[import]

                buf = StringStream()
                img.write(buf, "png")
                png_bytes: bytes = buf.getData()

                pil: Image.Image = Image.open(_io.BytesIO(png_bytes)).convert("RGB")
                out = _io.BytesIO()
                pil.save(out, format="JPEG", quality=jpeg_quality, optimize=True)

                jpeg_bytes = out.getvalue()
            except Exception:
                buf = StringStream()
                img.write(buf, "jpg")
                jpeg_bytes = buf.getData()

            ctx_mgr = getattr(sentry_sdk, "new_scope", None) or sentry_sdk.push_scope
            with ctx_mgr() as scope:  # type: ignore[misc]
                if tags:
                    for k, v in tags.items():
                        scope.set_tag(k, v)
                if extra:
                    for k, v in extra.items():
                        scope.set_extra(k, v)

                scope.set_context(
                    "runtime",
                    {
                        "python": cls.get_python_version(),
                        "panda3d": cls.get_panda_version(),
                        "kivy": cls.get_kivy_version(),
                        "git_commit": cls.get_git_commit(),
                        "git_branch": cls.get_git_branch(),
                    },
                )

                scope.add_attachment(
                    bytes=jpeg_bytes,
                    filename="screenshot.jpg",
                    content_type="image/jpeg",
                )

                return sentry_sdk.capture_message(message, level=level)
        except Exception as e:
            logging.exception("trigger_sentry_dump failed: %s", e)
            return None

    @classmethod
    def dump_map_generation_data(cls, generator: "BaseGenerator", tiles: List["Tile"]) -> None:
        json_data: bytes = json.dumps(cls.dump_map(generator.debug_dump_data, tiles))
        debug_dir: str = str(Path(PathsHelper.get_debug_dir()) / "map_dumps")
        timestamp: str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        if not Path(debug_dir).exists():
            Path(debug_dir).mkdir(parents=True, exist_ok=True)

        file_path: str = f"{debug_dir}/map_{timestamp}.json"
        fp: gzip.GzipFile = gzip.open(file_path + ".gz", "wb")
        fp.write(json_data)
        fp.close()

    @classmethod
    def dump_map(cls, data: Dict[str, Any], tiles: List["Tile"]) -> Dict[str, Any]:
        for tile in tiles:
            data["tiles"][f"{tile.x}, {tile.y}"] = cls.debug_dump_tile(tile)
        return data

    @classmethod
    def debug_dump_tile(cls, tile: "Tile") -> Dict[str, Any]:
        from gameplay.resource import BaseResource

        resources: List[BaseResource] = list(tile.resources.flatten_non_mechanic().values())
        resource: BaseResource | None = resources[0] if len(resources) > 0 else None
        data: Dict[str, Any] = {
            "x": tile.x,
            "y": tile.y,
            "altitude": tile.altitude,
            "temperature": tile.temperature,
            "moisture": tile.moisture,
            "terrain": tile.get_terrain().get_key(),
            "is_water": tile.is_water,
            "is_land": tile.is_land,
            "is_coast": tile.is_coast,
            "is_sea": tile.is_sea,
            "is_lake": tile.is_lake,
            "geoform_type": tile.geoforms,
            "features": [str(f) for f in tile.features],
            "resource": resource.key if resource else None,
        }
        return data


class PerformanceLogData:
    def __init__(self, real_time: datetime, zoom_level: float, camera_pos: Tuple[int, int, int], fps: float):
        self.real_time: datetime = real_time
        self.zoom_level: float = zoom_level
        self.camera_pos: Tuple[int, int, int] = camera_pos
        self.fps: float = fps

    def to_dict(self) -> Dict[str, Any]:
        return {
            "real_time": self.real_time.isoformat(),
            "zoom_level": self.zoom_level,
            "camera_pos": self.camera_pos,
            "fps": self.fps,
        }


class PerformanceLogger:
    PERFORMANCE_LOGGER_TICKS = 1 / 2  # log twice per second
    TASK_NAME = "PerformanceLogger"
    FLUSH_EVERY = 100

    def __init__(
        self,
        active_on_init: bool,
        location: str = "/performance_logs/performance_log.json",
        compress: bool = False,
    ):
        self.base = Cache.get_showbase_instance()
        self.start_time = datetime.now()
        self.active = active_on_init
        self.compress = compress

        data_dir = PathsHelper.get_data_dir()
        full_path = Path(data_dir) / location.lstrip("/")
        full_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path = str(full_path) + (".gz" if compress else "")

        mode = "ab" if compress else "a"
        opener = gzip.open if compress else io.open
        self.fp = opener(self.log_path, mode, encoding=None if compress else "utf-8")

        self._buffer: list[str] = []

        self.task: Optional[PythonTask] = None
        if self.active:
            self.activate()

    def activate(self) -> None:
        if not self.task:
            self.task = self.base.add_task(self._log_performance_tick, self.TASK_NAME, priority=0)

    def deactivate(self) -> None:
        self._flush_buffer()
        if self.task:
            self.base.remove_task(self.task)
            self.task = None
        try:
            self.fp.close()  # type: ignore
        except Exception:  # nosec: B110
            pass

    def _log_performance_tick(self, task: Task) -> Literal[1]:
        entry = self.generate_entry()
        self._buffer_entry(entry)
        return task.cont

    def _buffer_entry(self, entry: PerformanceLogData) -> None:
        delta = (entry.real_time - self.start_time).total_seconds()
        payload = {"t": delta, **entry.to_dict()}
        line = json.dumps(payload)

        self._buffer.append(line.decode("utf-8"))

        if len(self._buffer) >= self.FLUSH_EVERY:
            self._flush_buffer()

    def _flush_buffer(self) -> None:
        if not self._buffer:
            return

        for line in self._buffer:
            if self.compress:
                self.fp.write((line + "\n").encode("utf-8"))  # type: ignore
            else:
                self.fp.write(line + "\n")  # type: ignore
        try:
            self.fp.flush()  # type: ignore
            self._buffer.clear()
        except Exception:
            logging.warning("Failed to flush performance log to disk")

    @classmethod
    def get_zoom_level(cls) -> float:
        return Cache.get_showbase_instance().game_camera.zoom

    @classmethod
    def get_fps(cls) -> float:
        return ClockObject.getGlobalClock().getAverageFrameRate()

    @classmethod
    def get_camera_pos(cls) -> Tuple[int, int, int]:
        pos = Cache.get_showbase_instance().game_camera.getPos()  # type: ignore
        return tuple(map(int, (pos.x, pos.y, pos.z)))  #  type: ignore

    @classmethod
    def generate_entry(cls) -> PerformanceLogData:
        return PerformanceLogData(
            datetime.now(),
            zoom_level=cls.get_zoom_level(),
            camera_pos=cls.get_camera_pos(),
            fps=cls.get_fps(),
        )
