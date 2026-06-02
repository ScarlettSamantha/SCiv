import json
import os
from io import TextIOWrapper
from typing import Any, Dict, Optional, Tuple

from helpers.cache import Cache
from mixins.singleton import Singleton
from panda3d.core import WindowProperties, loadPrcFileData  # type: ignore

WINDOW_MODE_FULLSCREEN = "fullscreen"
WINDOW_MODE_BORDERLESS = "fullscreen-borderless"
WINDOW_MODE_WINDOW = "windowed"


type LayoutPosition = dict[str, float]


class ConfigManager(Singleton):
    config_data: Dict[str, Any] = {}
    config_file = "config.json"
    config_sample_file = "config_sample.json"
    world_generation_export_default_dir = "sciv/debugging/worldgen"

    def __setup__(self, *args: Any, **kwargs: Any) -> None:
        self.config_file = self.get_config_file_location()
        self.config_data = self._load_config()
        self.config_fp: Optional[TextIOWrapper] = None
        self.apply_config_to_prc()

    @classmethod
    def __call__(cls, *args: Any, **kwargs: Any) -> "ConfigManager":
        if not hasattr(cls, "_instance"):
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance

    @classmethod
    def get_config_file_location(cls) -> str:
        from helpers.paths import PathsHelper

        return PathsHelper.get_config_dir() + os.sep + cls.config_file

    def create_config_file(self) -> Optional[Dict[str, Any]]:
        from helpers.paths import PathsHelper

        config_dir = PathsHelper.get_config_dir()
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        sample_path = os.path.join(os.path.dirname(__file__), "../", self.config_sample_file)
        if not os.path.exists(sample_path):
            print(f"Sample config file '{self.config_sample_file}' not found. Cannot create default config.")
            return

        with open(sample_path, "r") as sample_file:
            default_config = json.load(sample_file)

        with open(self.config_file, "w") as f:
            json.dump(default_config, f, indent=4)
            print(f"Default config created at {self.config_file}")

        return default_config

    def _load_config(self) -> Any | Dict[str, Dict[str, bool] | Dict[str, str | int] | Dict[str, str | list[int]]]:
        path = os.path.abspath(self.config_file)
        if os.path.exists(path):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Failed to parse {self.config_file}: {e}")
        else:
            print(f"Config file '{self.config_file}' not found. Creating default config.")
            created_config_file: Optional[Dict[str, Any]] = self.create_config_file()
            if created_config_file is not None:
                return created_config_file
        raise RuntimeError(
            f"Config file '{self.config_file}' not found or invalid. Please create it with default settings."
        )

    def get_by_key(self, key: Tuple[str, ...], default: Optional[Any] = None, *args: Any) -> Any:
        data = self.config_data
        for k in key:
            if k in data:
                data = data[k]
            else:
                return default if default is not None else {}
        return data if data else default

    def get_config_full(self) -> Dict[str, Any]:
        return self.config_data

    def get_default(self, key: Tuple[str, ...], default: Any) -> Any:
        data = self.config_data
        for k in key:
            data = data.get(k, {})
        return data if data else default

    def set_by_key(self, value: Any, *args: Any):
        data = self.config_data
        for key in args[:-1]:
            data = data.setdefault(key, {})
        data[args[-1]] = value

    def save_config(self):
        if self.config_fp is None or self.config_fp.closed:
            self.config_fp = open(self.config_file, "w")
        with self.config_fp as f:
            try:
                json.dump(self.config_data, f, indent=4)
                print(f"Config saved to {self.config_file}")
            except Exception as e:
                print(f"Could not save config: {e}")

    def apply_config_to_prc(self):
        render_settings = self.config_data.get("render", {})
        for key, val in render_settings.items():
            loadPrcFileData("", f"{key} {val}")

        window_settings = self.config_data.get("window", {})

        screen_mode = window_settings.get("screen-mode", "windowed")  # fallback
        if screen_mode == "fullscreen":
            loadPrcFileData("", "fullscreen #t")
            loadPrcFileData("", "undecorated 0")
        elif screen_mode == "borderless":
            loadPrcFileData("", "fullscreen #f")
            loadPrcFileData("", "undecorated 1")
        else:
            loadPrcFileData("", "fullscreen #f")
            loadPrcFileData("", "undecorated 0")

        if "window-title" in window_settings:
            loadPrcFileData("", f"window-title {window_settings['window-title']}")

        if "win-origin" in window_settings:
            x, y = window_settings["win-origin"]
            loadPrcFileData("", f"win-origin {x} {y}")

        if "win-size" in window_settings:
            w, h = window_settings["win-size"]
            loadPrcFileData("", f"win-size {w} {h}")

        if "sync-video" in window_settings:
            loadPrcFileData("", "sync-video #t" if window_settings["sync-video"] else "sync-video #f")
            if window_settings["sync-video"]:
                os.environ["vblank_mode"] = "0"

        if "show-frame-rate-meter" in window_settings:
            loadPrcFileData("", f"show-frame-rate-meter {window_settings['show-frame-rate-meter']}")

        loadPrcFileData("", "window-icon-filename assets/logo_compact.png")

    def enable_vsync(self):
        self.config_data["window"]["sync-video"] = True
        os.environ["vblank_mode"] = "1"
        self.save_config()

    def disable_vsync(self):
        self.config_data["window"]["sync-video"] = False
        os.environ["vblank_mode"] = "0"
        self.save_config()

    def set_screen_mode(self, mode: str):
        self.config_data["window"]["screen-mode"] = mode
        props = WindowProperties()
        if mode == WINDOW_MODE_FULLSCREEN:
            props.setFullscreen(True)
            props.setUndecorated(False)
        elif mode == WINDOW_MODE_BORDERLESS:
            pipe = Cache.get_showbase_instance().win.getPipe()  # type: ignore

            props.setFullscreen(True)
            props.setUndecorated(True)
            Cache.get_showbase_instance().win.requestProperties(props)  # type: ignore
            screen_width = pipe.getDisplayWidth()
            screen_height = pipe.getDisplayHeight()
            props.setSize(screen_width, screen_height)

        elif mode == WINDOW_MODE_WINDOW:  # windowed
            props.setFullscreen(False)
            props.setUndecorated(False)
            Cache.get_showbase_instance().win.requestProperties(props)  # type: ignore # Need to first set it to windowed and then set the size
            props.setSize(1920, 1080)
        else:
            raise ValueError(f"Unknown screen mode: {mode}")
        Cache.get_showbase_instance().win.requestProperties(props)  # type: ignore
        self.save_config()

    def update_window_position_size(self, x: int, y: int, w: int, h: int):
        screen_mode = self.config_data["window"].get("screen-mode", "windowed")
        if screen_mode not in [WINDOW_MODE_FULLSCREEN, WINDOW_MODE_BORDERLESS]:
            self.config_data["window"]["win-origin"] = [x, y]
            self.config_data["window"]["win-size"] = [w, h]
            self.save_config()

    def toggle_fullscreen(self):
        current = self.config_data["window"].get("screen-mode", "windowed")
        if current != "fullscreen":
            self.set_screen_mode("fullscreen")
        else:
            self.set_screen_mode("windowed")

    def set_resolution(self, width: int, height: int, auto_save: bool = True):
        self.config_data["window"]["win-size"] = [width, height]
        props = WindowProperties()
        props.setSize(width, height)
        Cache.get_showbase_instance().win.requestProperties(props)  #  type: ignore
        if auto_save:
            self.save_config()

    def get_screen_mode(self) -> str:
        return self.config_data["window"].get("screen-mode", "windowed")

    def get_resolution(self) -> Tuple[int, int]:
        return tuple(self.config_data["window"].get("win-size", [1280, 720])[:2])

    def set_framerate_cap(self, fps: int):
        self.set_by_key(fps, "render", "clock-frame-rate")
        self.save_config()

    def enable_debug_mode(self):
        self.set_debug_mode(True)
        self.save_config()

    def disable_debug_mode(self):
        self.set_debug_mode(False)
        self.save_config()

    def set_debug_mode(self, enabled: bool, auto_save: bool = True):
        self.set_by_key(enabled, "debug", "enable")
        if auto_save:
            self.save_config()

    def toggle_debug_flag(self, flag: str, active: bool, auto_save: bool = True):
        self.config_data.setdefault("debug", {}).setdefault("debugs", {})[flag] = active
        if auto_save:
            self.save_config()

    def set_developer_mode(self, enabled: bool):
        self.set_by_key(enabled, "debug", "developer_mode")
        self.save_config()

    def set_fps_counter(self, enabled: bool):
        self.set_by_key(enabled, "debug", "fps_counter")
        self.save_config()

    def get_fps_counter(self) -> bool:
        return self.get_by_key(("debug", "fps_counter"), self.get_by_key(("debug", "fps-counter"), False))

    def get_developer_mode(self) -> bool:
        return self.get_by_key(("debug", "developer_mode"), False)

    def get_debug_mode(self) -> bool:
        return self.get_by_key(
            ("debug", "enable"),
            self.get_by_key(("debug", "enabled"), self.get_by_key(("debug", "enable_debug"), False)),
        )

    @staticmethod
    def _sanitize_positive_int(value: Any, default: int) -> int:
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            return default

    def get_world_generation_export_enabled(self) -> bool:
        return bool(self.get_by_key(("debug", "world_generation_export", "enabled"), False))

    def set_world_generation_export_enabled(self, enabled: bool, auto_save: bool = True) -> None:
        self.set_by_key(bool(enabled), "debug", "world_generation_export", "enabled")
        if auto_save:
            self.save_config()

    def get_world_generation_export_dir(self) -> str:
        configured = self.get_by_key(
            ("debug", "world_generation_export", "output_dir"),
            self.world_generation_export_default_dir,
        )
        if not isinstance(configured, str) or not configured.strip():
            return self.world_generation_export_default_dir
        return configured.strip()

    def set_world_generation_export_dir(self, output_dir: str, auto_save: bool = True) -> None:
        sanitized = output_dir.strip() if output_dir.strip() else self.world_generation_export_default_dir
        self.set_by_key(sanitized, "debug", "world_generation_export", "output_dir")
        if auto_save:
            self.save_config()

    def get_world_generation_export_batch_count(self) -> int:
        configured = self.get_by_key(("debug", "world_generation_export", "offline_batch_count"), 4)
        return self._sanitize_positive_int(configured, 4)

    def set_world_generation_export_batch_count(self, count: int, auto_save: bool = True) -> None:
        self.set_by_key(self._sanitize_positive_int(count, 4), "debug", "world_generation_export", "offline_batch_count")
        if auto_save:
            self.save_config()

    def get_ui_layout_drag_enabled(self) -> bool:
        return self.get_by_key(("debug", "ui_layout", "drag_enabled"), False)

    def set_ui_layout_drag_enabled(self, enabled: bool, auto_save: bool = True) -> None:
        self.set_by_key(enabled, "debug", "ui_layout", "drag_enabled")
        if auto_save:
            self.save_config()

    def get_ui_layout_overlay_enabled(self) -> bool:
        return self.get_by_key(("debug", "ui_layout", "show_overlay"), False)

    def set_ui_layout_overlay_enabled(self, enabled: bool, auto_save: bool = True) -> None:
        self.set_by_key(enabled, "debug", "ui_layout", "show_overlay")
        if auto_save:
            self.save_config()

    def get_ui_layout_positions(self) -> dict[str, LayoutPosition]:
        positions: dict[str, LayoutPosition] = self.get_by_key(("debug", "ui_layout", "positions"), {})
        return positions

    def set_ui_layout_position(self, widget_id: str, norm_x: float, norm_y: float, auto_save: bool = True) -> None:
        positions: dict[str, LayoutPosition] = self.config_data.setdefault("debug", {}).setdefault("ui_layout", {}).setdefault(
            "positions", {}
        )
        positions[widget_id] = {"x": norm_x, "y": norm_y}
        if auto_save:
            self.save_config()

    def get_ui_layout_position(self, widget_id: str) -> LayoutPosition | None:
        return self.get_ui_layout_positions().get(widget_id)

    def reset_ui_layout_positions(self, auto_save: bool = True) -> None:
        self.set_by_key({}, "debug", "ui_layout", "positions")
        if auto_save:
            self.save_config()

    def get_debug_flags(self) -> Dict[str, bool]:
        return self.get_by_key(("debug", "debugs"), {})

    def get_debug_flag(self, flag: str) -> bool:
        return self.get_by_key(("debug", "debugs", flag), False)

    def get_available_languages(self) -> Dict[str, str]:
        return self.get_by_key(("languages", "available"), {})

    def get_default_language(self) -> str:
        return self.get_by_key(("languages", "default"), "en_EN")

    def get_language(self) -> str:
        return self.get_by_key(("languages", "selected"), "")

    def set_language(self, language: str, auto_save: bool = True):
        if language not in self.get_available_languages():
            raise ValueError(f"Language '{language}' is not available.")

        self.set_by_key(language, "languages", "selected")
        if auto_save:
            self.save_config()

    def get_mouse_lock(self) -> bool:
        return self.get_by_key(("ui", "mouse_lock"), False)

    def set_mouse_lock(self, enabled: bool, auto_save: bool = True):
        self.set_by_key(enabled, "ui", "mouse_lock")
        if auto_save:
            self.save_config()
