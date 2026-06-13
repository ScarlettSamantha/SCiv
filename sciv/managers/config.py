import json
import os
import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple, cast

from direct.task.Task import done

from helpers.cache import Cache
from mixins.singleton import Singleton
from panda3d.core import WindowProperties, loadPrcFileData  # type: ignore

WINDOW_MODE_FULLSCREEN = "fullscreen"
WINDOW_MODE_BORDERLESS = "fullscreen-borderless"
WINDOW_MODE_WINDOW = "windowed"
WINDOW_MONITOR_AUTO = "auto"

LayoutPosition = Dict[str, float]
MonitorInfo = Dict[str, int | str]

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
        screen_mode = str(window_settings.get("screen-mode", WINDOW_MODE_WINDOW))
        monitor = self._get_effective_monitor_info()
        width, height = self.get_resolution()

        loadPrcFileData("", "win-fixed-size #f")

        if screen_mode in [WINDOW_MODE_FULLSCREEN, WINDOW_MODE_BORDERLESS] and monitor is not None:
            x, y, w, h = self._monitor_geometry(monitor)
            loadPrcFileData("", f"win-origin {x} {y}")
            loadPrcFileData("", f"win-size {w} {h}")
        elif screen_mode == WINDOW_MODE_WINDOW:
            origin = self._resolve_windowed_origin(width, height)
            if origin is not None:
                x, y = origin
                loadPrcFileData("", f"win-origin {x} {y}")
            loadPrcFileData("", f"win-size {width} {height}")
        elif "win-size" in window_settings:
            w, h = window_settings["win-size"]
            loadPrcFileData("", f"win-size {w} {h}")

        if screen_mode == WINDOW_MODE_FULLSCREEN:
            loadPrcFileData("", "fullscreen #t")
            loadPrcFileData("", "undecorated #f")
        elif screen_mode == WINDOW_MODE_BORDERLESS:
            loadPrcFileData("", "fullscreen #t")
            loadPrcFileData("", "undecorated #f")
        else:
            loadPrcFileData("", "fullscreen #f")
            loadPrcFileData("", "undecorated #f")

        if "window-title" in window_settings:
            loadPrcFileData("", f"window-title {window_settings['window-title']}")

        if "sync-video" in window_settings:
            loadPrcFileData("", "sync-video #t" if window_settings["sync-video"] else "sync-video #f")
            os.environ["vblank_mode"] = "1" if window_settings["sync-video"] else "0"

        if "show-frame-rate-meter" in window_settings:
            loadPrcFileData("", f"show-frame-rate-meter {window_settings['show-frame-rate-meter']}")

        loadPrcFileData("", "window-icon-filename assets/logo_compact.png")

    def _get_xrandr_monitors(self) -> List[MonitorInfo]:
        monitors: List[MonitorInfo] = []
        pattern = re.compile(
            r"^(?P<name>\S+)\s+connected(?:\s+primary)?(?:\s+(?P<w>\d+)x(?P<h>\d+)(?P<x>[+-]\d+)(?P<y>[+-]\d+))?"
        )

        try:
            result = subprocess.run(
                ["xrandr", "--query"],
                check=False,
                capture_output=True,
                text=True,
                timeout=1.0,
            )
        except (OSError, subprocess.SubprocessError):
            return monitors

        if result.returncode != 0:
            return monitors

        for line in result.stdout.splitlines():
            match = pattern.match(line.strip())
            if match is None or match.group("w") is None:
                continue

            monitor_name = match.group("name")
            monitors.append(
                {
                    "id": monitor_name,
                    "name": monitor_name,
                    "x": int(match.group("x")),
                    "y": int(match.group("y")),
                    "width": int(match.group("w")),
                    "height": int(match.group("h")),
                }
            )

        monitors.sort(key=lambda monitor: (int(monitor["x"]), int(monitor["y"]), str(monitor["name"])))
        return monitors

    def _get_fallback_monitor(self) -> MonitorInfo:
        width, height = self.get_resolution()

        try:
            win = Cache.get_showbase_instance().win  # type: ignore
            pipe = win.getPipe()
            display_width = int(pipe.getDisplayWidth())
            display_height = int(pipe.getDisplayHeight())
            if display_width > 0 and display_height > 0:
                width = display_width
                height = display_height
        except Exception:
            pass

        return {
            "id": "0",
            "name": "Display",
            "x": 0,
            "y": 0,
            "width": max(1, width),
            "height": max(1, height),
        }

    def get_available_monitors(self) -> List[MonitorInfo]:
        monitors = self._get_xrandr_monitors()
        if monitors:
            return monitors
        return [self._get_fallback_monitor()]

    def get_monitor_options(self) -> Dict[str, str]:
        options: Dict[str, str] = {WINDOW_MONITOR_AUTO: "Auto / last used monitor"}

        for index, monitor in enumerate(self.get_available_monitors(), start=1):
            monitor_id = str(monitor["id"])
            name = str(monitor["name"])
            x, y, width, height = self._monitor_geometry(monitor)
            options[monitor_id] = f"Monitor {index}: {name} - {width}x{height} at {x},{y}"

        return options

    def get_monitor_label(self, monitor_id: str | None = None) -> str:
        selected = self.get_monitor() if monitor_id is None else self._normalize_monitor_id(monitor_id)
        options = self.get_monitor_options()
        return options.get(selected, options[WINDOW_MONITOR_AUTO])

    def get_monitor(self) -> str:
        window_settings = self.config_data.setdefault("window", {})
        value = window_settings.get("monitor", WINDOW_MONITOR_AUTO)
        if not isinstance(value, str) or not value.strip():
            return WINDOW_MONITOR_AUTO

        normalized = self._normalize_monitor_id(value.strip())
        if normalized != value:
            window_settings["monitor"] = normalized
        return normalized

    def set_monitor(self, monitor_id: str, auto_save: bool = True, apply_now: bool = True) -> None:
        normalized = self._normalize_monitor_id(monitor_id.strip() if monitor_id.strip() else WINDOW_MONITOR_AUTO)
        if normalized != WINDOW_MONITOR_AUTO and self._get_monitor_by_id(normalized) is None:
            normalized = WINDOW_MONITOR_AUTO

        self.config_data.setdefault("window", {})["monitor"] = normalized

        if apply_now:
            self.set_screen_mode(self.get_screen_mode(), auto_save=False)

        if auto_save:
            self.save_config()

    def _normalize_monitor_id(self, monitor_id: str) -> str:
        if monitor_id == WINDOW_MONITOR_AUTO:
            return WINDOW_MONITOR_AUTO

        monitors = self.get_available_monitors()
        if monitor_id.isdigit():
            index = int(monitor_id)
            if 0 <= index < len(monitors):
                return str(monitors[index]["id"])

        for monitor in monitors:
            if str(monitor["id"]) == monitor_id or str(monitor["name"]) == monitor_id:
                return str(monitor["id"])

        return monitor_id

    def _get_monitor_by_id(self, monitor_id: str) -> MonitorInfo | None:
        normalized = self._normalize_monitor_id(monitor_id)
        for monitor in self.get_available_monitors():
            if str(monitor["id"]) == normalized:
                return monitor
        return None

    def _monitor_geometry(self, monitor: MonitorInfo) -> Tuple[int, int, int, int]:
        return int(monitor["x"]), int(monitor["y"]), int(monitor["width"]), int(monitor["height"])

    def _window_center(self, x: int, y: int, width: int, height: int) -> Tuple[int, int]:
        return x + max(1, width) // 2, y + max(1, height) // 2

    def _point_is_inside_monitor(self, point_x: int, point_y: int, monitor: MonitorInfo) -> bool:
        x, y, width, height = self._monitor_geometry(monitor)
        return x <= point_x < x + width and y <= point_y < y + height

    def _window_is_on_monitor(self, x: int, y: int, width: int, height: int, monitor: MonitorInfo) -> bool:
        center_x, center_y = self._window_center(x, y, width, height)
        return self._point_is_inside_monitor(center_x, center_y, monitor)

    def _get_monitor_for_window(self, x: int, y: int, width: int, height: int) -> MonitorInfo | None:
        center_x, center_y = self._window_center(x, y, width, height)
        for monitor in self.get_available_monitors():
            if self._point_is_inside_monitor(center_x, center_y, monitor):
                return monitor
        return None

    def _get_effective_monitor_info(self) -> MonitorInfo | None:
        selected_monitor = self.get_monitor()
        if selected_monitor != WINDOW_MONITOR_AUTO:
            return self._get_monitor_by_id(selected_monitor)

        x, y = self.get_window_origin()
        width, height = self.get_resolution()
        return self._get_monitor_for_window(x, y, width, height)

    def _resolve_windowed_origin(self, width: int, height: int) -> Tuple[int, int] | None:
        saved_x, saved_y = self.get_window_origin()
        selected_monitor = self.get_monitor()

        if selected_monitor == WINDOW_MONITOR_AUTO:
            return saved_x, saved_y

        monitor = self._get_monitor_by_id(selected_monitor)
        if monitor is None:
            return saved_x, saved_y

        if self._window_is_on_monitor(saved_x, saved_y, width, height, monitor):
            return saved_x, saved_y

        monitor_x, monitor_y, monitor_width, monitor_height = self._monitor_geometry(monitor)
        offset_x = max(0, min(80, max(0, monitor_width - width) // 2))
        offset_y = max(0, min(80, max(0, monitor_height - height) // 2))
        return monitor_x + offset_x, monitor_y + offset_y

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

    def set_screen_mode(self, mode: str, auto_save: bool = True) -> None:
        window_settings = self.config_data.setdefault("window", {})
        window_settings["screen-mode"] = mode

        if mode == WINDOW_MODE_FULLSCREEN:
            monitor = self._get_effective_monitor_info() or self._get_fallback_monitor()
            x, y, width, height = self._monitor_geometry(monitor)
            window_settings["win-origin"] = [x, y]
            window_settings["win-size"] = [width, height]
            self._request_fullscreen_properties(x, y, width, height, undecorated=False)
        elif mode == WINDOW_MODE_BORDERLESS:
            monitor = self._get_effective_monitor_info() or self._get_fallback_monitor()
            x, y, width, height = self._monitor_geometry(monitor)
            window_settings["win-origin"] = [x, y]
            window_settings["win-size"] = [width, height]
            self._request_fullscreen_properties(x, y, width, height, undecorated=False)
        elif mode == WINDOW_MODE_WINDOW:
            width, height = self.get_resolution()
            origin = self._resolve_windowed_origin(width, height)
            props = WindowProperties()
            props.setFullscreen(False)
            props.setUndecorated(False)
            props.setSize(width, height)

            if origin is not None:
                x, y = origin
                window_settings["win-origin"] = [x, y]
                props.setOrigin(x, y)

            Cache.get_showbase_instance().win.requestProperties(props)  # type: ignore
        else:
            raise ValueError(f"Unknown screen mode: {mode}")

        if auto_save:
            self.save_config()

    def _request_fullscreen_properties(self, x: int, y: int, width: int, height: int, undecorated: bool) -> None:
        base = Cache.get_showbase_instance()

        leave_props = WindowProperties()
        leave_props.setFullscreen(False)
        leave_props.setUndecorated(False)
        leave_props.setOrigin(x, y)
        leave_props.setSize(width, height)
        base.win.requestProperties(leave_props)  # type: ignore

        def apply_fullscreen(task: Any) -> int:
            fullscreen_props = WindowProperties()
            fullscreen_props.setOrigin(x, y)
            fullscreen_props.setSize(width, height)
            fullscreen_props.setFullscreen(True)
            fullscreen_props.setUndecorated(undecorated)
            base.win.requestProperties(fullscreen_props)  # type: ignore
            return done

        base.taskMgr.remove("apply-configured-window-monitor")
        base.taskMgr.doMethodLater(0.08, apply_fullscreen, "apply-configured-window-monitor")

    def update_window_size(self, width: int, height: int, auto_save: bool = True) -> None:
        origin_x, origin_y = self.get_window_origin()
        self.update_window_position_size(origin_x, origin_y, width, height, auto_save=auto_save)

    def update_window_position_size(self, x: int, y: int, w: int, h: int, auto_save: bool = True) -> None:
        window_settings = self.config_data.setdefault("window", {})
        screen_mode = window_settings.get("screen-mode", WINDOW_MODE_WINDOW)

        if screen_mode != WINDOW_MODE_WINDOW:
            return

        sanitized_x = int(x)
        sanitized_y = int(y)
        sanitized_width = max(1, int(w))
        sanitized_height = max(1, int(h))

        current_origin = window_settings.get("win-origin", [])
        current_size = window_settings.get("win-size", [])
        selected_monitor = self.get_monitor()

        changed = current_origin != [sanitized_x, sanitized_y] or current_size != [sanitized_width, sanitized_height]
        window_settings["win-origin"] = [sanitized_x, sanitized_y]
        window_settings["win-size"] = [sanitized_width, sanitized_height]

        monitor = self._get_monitor_for_window(sanitized_x, sanitized_y, sanitized_width, sanitized_height)
        if selected_monitor != WINDOW_MONITOR_AUTO and monitor is not None:
            monitor_id = str(monitor["id"])
            if window_settings.get("monitor") != monitor_id:
                window_settings["monitor"] = monitor_id
                changed = True

        if changed and auto_save:
            self.save_config()

    def toggle_fullscreen(self) -> None:
        current = self.config_data.setdefault("window", {}).get("screen-mode", WINDOW_MODE_WINDOW)
        if current != WINDOW_MODE_FULLSCREEN:
            self.set_screen_mode(WINDOW_MODE_FULLSCREEN)
        else:
            self.set_screen_mode(WINDOW_MODE_WINDOW)

    def set_resolution(self, width: int, height: int, auto_save: bool = True) -> None:
        window_settings = self.config_data.setdefault("window", {})
        sanitized_width = max(1, int(width))
        sanitized_height = max(1, int(height))
        window_settings["win-size"] = [sanitized_width, sanitized_height]

        if self.get_screen_mode() == WINDOW_MODE_WINDOW:
            props = WindowProperties()
            origin = self._resolve_windowed_origin(sanitized_width, sanitized_height)
            props.setSize(sanitized_width, sanitized_height)
            if origin is not None:
                x, y = origin
                props.setOrigin(x, y)
                window_settings["win-origin"] = [x, y]
            Cache.get_showbase_instance().win.requestProperties(props)  # type: ignore

        if auto_save:
            self.save_config()

    def get_screen_mode(self) -> str:
        return str(self.config_data.setdefault("window", {}).get("screen-mode", WINDOW_MODE_WINDOW))

    def get_resolution(self) -> Tuple[int, int]:
        configured = self.config_data.setdefault("window", {}).get("win-size", [1280, 720])
        return int(configured[0]), int(configured[1])

    def get_window_origin(self) -> Tuple[int, int]:
        configured = self.config_data.setdefault("window", {}).get("win-origin", [0, 0])
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
