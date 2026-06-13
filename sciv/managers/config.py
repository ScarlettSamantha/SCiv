import json
import os
from typing import Any, Dict, Optional, Tuple, cast

from helpers.cache import Cache
from mixins.singleton import Singleton
from panda3d.core import WindowProperties, loadPrcFileData  # type: ignore

WINDOW_MODE_FULLSCREEN = "fullscreen"
WINDOW_MODE_BORDERLESS = "fullscreen-borderless"
WINDOW_MODE_WINDOW = "windowed"

LayoutPosition = Dict[str, float]

type json_data = str | int | bool | Dict[str, Any] | list[Any] | None

class ConfigManager(Singleton):
    config_data: Dict[str, Any] = {}
    config_file = "config.json"
    config_sample_file = "config_sample.json"
    world_generation_export_default_dir = "sciv/debugging/worldgen"

    def __setup__(self, *args: Any, **kwargs: Any) -> None:
        self.config_file = self.get_config_file_location()
        self.config_data = self._load_config()
        self.apply_config_to_prc()
        self._sync_debug_runtime_state()

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
            return None

        with open(sample_path, "r", encoding="utf-8") as sample_file:
            default_config: Dict[str, Any] = json.load(sample_file)

        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)
            f.write("\n")
            print(f"Default config created at {self.config_file}")

        return default_config

    def _load_config(self) -> Dict[str, Any]:
        path = os.path.abspath(self.config_file)
        if os.path.exists(path):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded: Dict[str, Any] = json.load(f)
                    return loaded
            except Exception as e:
                print(f"Failed to parse {self.config_file}: {e}")
        else:
            print(f"Config file '{self.config_file}' not found. Creating default config.")
            created_config_file = self.create_config_file()
            if created_config_file is not None:
                return created_config_file
        raise RuntimeError(
            f"Config file '{self.config_file}' not found or invalid. Please create it with default settings."
        )

    def get_by_key(self, key: Tuple[str, ...], default: Optional[Any] = None, *args: Any) -> json_data:
        data: Any = self.config_data
        for k in key:
            if isinstance(data, dict) and k in data:
                data = cast(Dict[str, Any], data)[k]
            else:
                return default if default is not None else {}
        return data

    def get_config_full(self) -> Dict[str, Any]:
        return self.config_data

    def get_default(self, key: Tuple[str, ...], default: Any) -> Any:
        data: Any = self.config_data
        for k in key:
            if not isinstance(data, dict):
                return default
            data = cast(Dict[str, Any], data).get(k, {})
        return data if data != {} else default

    def set_by_key(self, value: Any, *args: str) -> None:
        if not args:
            raise ValueError("set_by_key requires at least one key.")

        data: Dict[str, Any] = self.config_data
        for key in args[:-1]:
            child: Any = data.get(key)
            if not isinstance(child, dict):
                child = {}
                data[key] = child
            data = cast(Dict[str, Any], child)
        data[args[-1]] = value

    def save_config(self) -> None:
        config_dir = os.path.dirname(os.path.abspath(self.config_file))
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)

        temp_file = f"{self.config_file}.tmp"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=4)
                f.write("\n")
            os.replace(temp_file, self.config_file)
            print(f"Config saved to {self.config_file}")
        except Exception as e:
            print(f"Could not save config: {e}")
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass

    def apply_config_to_prc(self) -> None:
        render_settings = self.config_data.get("render", {})
        for key, val in render_settings.items():
            loadPrcFileData("", f"{key} {val}")

        window_settings = self.config_data.get("window", {})

        screen_mode = window_settings.get("screen-mode", "windowed")
        if screen_mode == WINDOW_MODE_FULLSCREEN:
            loadPrcFileData("", "fullscreen #t")
            loadPrcFileData("", "undecorated 0")
        elif screen_mode == WINDOW_MODE_BORDERLESS:
            loadPrcFileData("", "fullscreen #t")
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
            os.environ["vblank_mode"] = "1" if window_settings["sync-video"] else "0"

        if "show-frame-rate-meter" in window_settings:
            loadPrcFileData("", f"show-frame-rate-meter {window_settings['show-frame-rate-meter']}")

        loadPrcFileData("", "window-icon-filename assets/logo_compact.png")

    def _sync_debug_runtime_state(self) -> None:
        try:
            from helpers.debug import Debug, Debugs

            Debug.config_instance_ref = self
            Debug.debug = self.get_debug_mode()
            Debug.debug_modes = {
                Debugs.WORLD_GENERATION: self.get_debug_flag(Debugs.WORLD_GENERATION.value),
                Debugs.WORLD_SPAWNING: self.get_debug_flag(Debugs.WORLD_SPAWNING.value),
                Debugs.SYSTEM_LOADING_CLASSES: self.get_debug_flag(Debugs.SYSTEM_LOADING_CLASSES.value),
                Debugs.SYSTEM_LOADING_MODELS: self.get_debug_flag(Debugs.SYSTEM_LOADING_MODELS.value),
                Debugs.SYSTEM_ASSET_GENERATION: self.get_debug_flag(Debugs.SYSTEM_ASSET_GENERATION.value),
                Debugs.DISABLE_AI_TURN_PROCESSING: self.get_disable_ai_turn_processing(),
                Debugs.SYSTEM_AI: self.get_debug_flag(Debugs.SYSTEM_AI.value),
                Debugs.SYSTEM_SAVING: self.get_debug_flag(Debugs.SYSTEM_SAVING.value),
                Debugs.SYSTEM_LOADING: self.get_debug_flag(Debugs.SYSTEM_LOADING.value),
                Debugs.SYSTEM_ENTITY_GRAPH: self.get_debug_flag(Debugs.SYSTEM_ENTITY_GRAPH.value),
                Debugs.SYSTEM_PERFORMANCE_LOGGING: self.get_debug_flag(Debugs.SYSTEM_PERFORMANCE_LOGGING.value),
                Debugs.SYSTEM_INPUT: self.get_debug_flag(Debugs.SYSTEM_INPUT.value),
                Debugs.SYSTEM_UNITS: self.get_debug_flag(Debugs.SYSTEM_UNITS.value),
            }
        except Exception:
            pass

    def _notify_debug_config_changed(self) -> None:
        self._sync_debug_runtime_state()
        try:
            from direct.showbase.MessengerGlobal import messenger

            messenger.send("config.debug.changed", [self.get_debug_mode()])
        except Exception:
            pass

    def enable_vsync(self) -> None:
        self.config_data.setdefault("window", {})["sync-video"] = True
        os.environ["vblank_mode"] = "1"
        self.save_config()

    def disable_vsync(self) -> None:
        self.config_data.setdefault("window", {})["sync-video"] = False
        os.environ["vblank_mode"] = "0"
        self.save_config()

    def set_screen_mode(self, mode: str) -> None:
        self.config_data.setdefault("window", {})["screen-mode"] = mode
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
        elif mode == WINDOW_MODE_WINDOW:
            props.setFullscreen(False)
            props.setUndecorated(False)
            Cache.get_showbase_instance().win.requestProperties(props)  # type: ignore
            props.setSize(1920, 1080)
        else:
            raise ValueError(f"Unknown screen mode: {mode}")
        Cache.get_showbase_instance().win.requestProperties(props)  # type: ignore
        self.save_config()

    def update_window_position_size(self, x: int, y: int, w: int, h: int) -> None:
        screen_mode = self.config_data.setdefault("window", {}).get("screen-mode", WINDOW_MODE_WINDOW)
        if screen_mode not in [WINDOW_MODE_FULLSCREEN, WINDOW_MODE_BORDERLESS]:
            self.config_data["window"]["win-origin"] = [x, y]
            self.config_data["window"]["win-size"] = [w, h]
            self.save_config()

    def toggle_fullscreen(self) -> None:
        current = self.config_data.setdefault("window", {}).get("screen-mode", WINDOW_MODE_WINDOW)
        if current != WINDOW_MODE_FULLSCREEN:
            self.set_screen_mode(WINDOW_MODE_FULLSCREEN)
        else:
            self.set_screen_mode(WINDOW_MODE_WINDOW)

    def set_resolution(self, width: int, height: int, auto_save: bool = True) -> None:
        self.config_data.setdefault("window", {})["win-size"] = [width, height]
        props = WindowProperties()
        props.setSize(width, height)
        Cache.get_showbase_instance().win.requestProperties(props)  # type: ignore
        if auto_save:
            self.save_config()

    def get_screen_mode(self) -> str:
        return str(self.config_data.setdefault("window", {}).get("screen-mode", WINDOW_MODE_WINDOW))

    def get_resolution(self) -> Tuple[int, int]:
        configured = self.config_data.setdefault("window", {}).get("win-size", [1280, 720])
        return int(configured[0]), int(configured[1])

    def set_framerate_cap(self, fps: int, auto_save: bool = True) -> None:
        self.set_by_key(int(fps), "render", "clock-frame-rate")
        if auto_save:
            self.save_config()

    def enable_debug_mode(self) -> None:
        self.set_debug_mode(True)

    def disable_debug_mode(self) -> None:
        self.set_debug_mode(False)

    def set_debug_mode(self, enabled: bool, auto_save: bool = True) -> None:
        self.set_by_key(bool(enabled), "debug", "enable")
        self._notify_debug_config_changed()
        if auto_save:
            self.save_config()

    def toggle_debug_flag(self, flag: str, active: bool, auto_save: bool = True) -> None:
        self.set_by_key(bool(active), "debug", "debugs", flag)
        self._notify_debug_config_changed()
        if auto_save:
            self.save_config()

    def set_developer_mode(self, enabled: bool, auto_save: bool = True) -> None:
        self.set_by_key(bool(enabled), "debug", "developer_mode")
        if auto_save:
            self.save_config()

    def set_fps_counter(self, enabled: bool, auto_save: bool = True) -> None:
        self.set_by_key(bool(enabled), "debug", "fps_counter")
        self.set_by_key(bool(enabled), "window", "show-frame-rate-meter")
        loadPrcFileData("", f"show-frame-rate-meter {bool(enabled)}")
        if auto_save:
            self.save_config()

    def get_fps_counter(self) -> bool:
        return bool(self.get_by_key(("debug", "fps_counter"), self.get_by_key(("debug", "fps-counter"), False)))

    def get_developer_mode(self) -> bool:
        return bool(self.get_by_key(("debug", "developer_mode"), False))

    def get_debug_mode(self) -> bool:
        return bool(
            self.get_by_key(
                ("debug", "enable"),
                self.get_by_key(("debug", "enabled"), self.get_by_key(("debug", "enable_debug"), False)),
            )
        )

    def get_cheat_menu(self) -> bool:
        return bool(self.get_by_key(("debug", "cheat_menu"), False))

    def set_cheat_menu(self, enabled: bool, auto_save: bool = True) -> None:
        self.set_by_key(bool(enabled), "debug", "cheat_menu")
        if auto_save:
            self.save_config()

    def get_confirm_exit(self) -> bool:
        return bool(self.get_by_key(("ui", "confirm_exit"), True))

    def set_confirm_exit(self, enabled: bool, auto_save: bool = True) -> None:
        self.set_by_key(bool(enabled), "ui", "confirm_exit")
        if auto_save:
            self.save_config()

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
        self._notify_debug_config_changed()
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

    def get_disable_ai_turn_processing(self) -> bool:
        return bool(self.get_by_key(("debug", "disable_ai_turn_processing"), False))

    def set_disable_ai_turn_processing(self, enabled: bool, auto_save: bool = True) -> None:
        self.set_by_key(bool(enabled), "debug", "disable_ai_turn_processing")
        self._notify_debug_config_changed()
        if auto_save:
            self.save_config()

    def get_sentry_enabled(self) -> bool:
        return bool(self.get_by_key(("debug", "sentry", "enable"), False))

    def set_sentry_enabled(self, enabled: bool, auto_save: bool = True) -> None:
        self.set_by_key(bool(enabled), "debug", "sentry", "enable")
        if auto_save:
            self.save_config()

    def get_sentry_dsn(self) -> str:
        dsn = self.get_by_key(("debug", "sentry", "dsn"), "")
        return dsn if isinstance(dsn, str) else ""

    def set_sentry_dsn(self, dsn: str, auto_save: bool = True) -> None:
        self.set_by_key(dsn.strip(), "debug", "sentry", "dsn")
        if auto_save:
            self.save_config()

    def get_ui_layout_drag_enabled(self) -> bool:
        return bool(self.get_by_key(("debug", "ui_layout", "drag_enabled"), False))

    def set_ui_layout_drag_enabled(self, enabled: bool, auto_save: bool = True) -> None:
        self.set_by_key(bool(enabled), "debug", "ui_layout", "drag_enabled")
        self._notify_debug_config_changed()
        if auto_save:
            self.save_config()

    def get_ui_layout_overlay_enabled(self) -> bool:
        return bool(self.get_by_key(("debug", "ui_layout", "show_overlay"), False))

    def set_ui_layout_overlay_enabled(self, enabled: bool, auto_save: bool = True) -> None:
        self.set_by_key(bool(enabled), "debug", "ui_layout", "show_overlay")
        self._notify_debug_config_changed()
        if auto_save:
            self.save_config()

    def get_ui_layout_positions(self) -> Dict[str, LayoutPosition]:
        positions = self.get_by_key(("debug", "ui_layout", "positions"), {})
        return cast(Dict[str, LayoutPosition], positions) if isinstance(positions, dict) else {}

    def set_ui_layout_position(self, widget_id: str, norm_x: float, norm_y: float, auto_save: bool = True) -> None:
        positions: Dict[str, LayoutPosition] = self.config_data.setdefault("debug", {}).setdefault("ui_layout", {}).setdefault(
            "positions", {}
        )
        positions[widget_id] = {"x": norm_x, "y": norm_y}
        if auto_save:
            self.save_config()

    def get_ui_layout_position(self, widget_id: str) -> LayoutPosition | None:
        return self.get_ui_layout_positions().get(widget_id)

    def reset_ui_layout_positions(self, auto_save: bool = True) -> None:
        self.set_by_key({}, "debug", "ui_layout", "positions")
        self._notify_debug_config_changed()
        if auto_save:
            self.save_config()

    def get_debug_flags(self) -> Dict[str, bool]:
        flags = self.get_by_key(("debug", "debugs"), {})
        return cast(Dict[str, bool], flags) if isinstance(flags, dict) else {}

    def get_debug_flag(self, flag: str) -> bool:
        return bool(self.get_by_key(("debug", "debugs", flag), False))

    def get_available_languages(self) -> Dict[str, str]:
        configured = self.get_by_key(("languages", "available"), {})
        if isinstance(configured, list):
            return {str(value): str(value) for value in configured}
        return cast(Dict[str, str], configured) if isinstance(configured, dict) else {}

    def get_default_language(self) -> str:
        return str(self.get_by_key(("languages", "default"), "en_EN"))

    def get_language(self) -> str:
        selected = self.get_by_key(("languages", "selected"), self.get_default_language())
        return str(selected or self.get_default_language())

    def set_language(self, language: str, auto_save: bool = True) -> None:
        if language not in self.get_available_languages():
            raise ValueError(f"Language '{language}' is not available.")

        self.set_by_key(language, "languages", "selected")
        if auto_save:
            self.save_config()

    def get_mouse_lock(self) -> bool:
        return bool(self.get_by_key(("ui", "mouse_lock"), False))

    def set_mouse_lock(self, enabled: bool, auto_save: bool = True) -> None:
        self.set_by_key(bool(enabled), "ui", "mouse_lock")
        if auto_save:
            self.save_config()
