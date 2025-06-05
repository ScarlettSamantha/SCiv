import json
import os
from typing import Any, Dict, Tuple

from panda3d.core import loadPrcFileData  # type: ignore

from mixins.singleton import Singleton


class ConfigManager(Singleton):
    config_data: Dict[str, Any] = {}
    config_file = "config.json"

    def __setup__(self, *args: Any, **kwargs: Any) -> None:
        self.config_file = self.config_file
        self.config_data = self._load_config()
        self.apply_config_to_prc()
        return super().__setup__(*args, **kwargs)

    def _load_config(self) -> Any | Dict[str, Dict[str, bool] | Dict[str, str | int] | Dict[str, str | list[int]]]:
        """Internal method: load config from JSON or return default if missing/invalid."""
        path = os.path.abspath(self.config_file)
        if os.path.exists(path):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Failed to parse {self.config_file}: {e}")

        # If not found or failed, return a reasonable default:
        raise RuntimeError(
            f"Config file '{self.config_file}' not found or invalid. Please create it with default settings."
        )

    def get_by_key(self, *args: Any) -> Any:
        """
        Get a value from the config by key.
        Example: get_by_key("window", "win-size") -> [1280, 720]
        """
        data = self.config_data
        for key in args:
            data = data.get(key, {})  # type: ignore
        return data  # type: ignore

    def get_config_full(self) -> Dict[str, Any]:
        """Return the full config data."""
        return self.config_data

    def get_default(self, key: Tuple[str, ...], default: Any) -> Any:
        """
        Get a value from the config by a single key.
        Example: get("window") -> {"win-size": [1280, 720], ...}
        """
        data = self.config_data
        for k in key:
            data = data.get(k, {})
        return data if data else default

    def set_by_key(self, value: Any, *args: Any):
        """
        Set a value in the config by key.
        Example: set_by_key([1280, 720], "window", "win-size")
        """
        data = self.config_data
        for key in args[:-1]:
            data = data.get(key, {})
        data[args[-1]] = value

    def save_config(self):
        """Persist current config to the JSON file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config_data, f, indent=2)
        except Exception as e:
            print(f"Could not save config: {e}")

    def apply_config_to_prc(self):
        """
        Read config_data and apply it to Panda3D via loadPrcFileData.
        This should be called BEFORE ShowBase is constructed.
        """
        # 1) Render / FPS settings
        render_settings = self.config_data.get("render", {})
        for key, val in render_settings.items():
            loadPrcFileData("", f"{key} {val}")

        # 2) Window settings
        window_settings = self.config_data.get("window", {})

        # Screen mode
        screen_mode = window_settings.get("screen-mode", "windowed")  # fallback
        if screen_mode == "fullscreen":
            # OS fullscreen
            loadPrcFileData("", "fullscreen #t")
            loadPrcFileData("", "undecorated 0")
        elif screen_mode == "borderless":
            # Borderless window -> typically same as fullscreen but "fullscreen #f"
            # so it can be sized to the user's monitor resolution.
            loadPrcFileData("", "fullscreen #f")
            loadPrcFileData("", "undecorated 1")
        else:
            # Normal window
            loadPrcFileData("", "fullscreen #f")
            loadPrcFileData("", "undecorated 0")

        # Window title
        if "window-title" in window_settings:
            loadPrcFileData("", f"window-title {window_settings['window-title']}")

        # Window origin (only relevant if not OS fullscreen)
        if "win-origin" in window_settings:
            x, y = window_settings["win-origin"]
            loadPrcFileData("", f"win-origin {x} {y}")

        # Window size
        if "win-size" in window_settings:
            w, h = window_settings["win-size"]
            loadPrcFileData("", f"win-size {w} {h}")

        if "sync-video" in window_settings:
            loadPrcFileData("", "sync-video #t" if window_settings["sync-video"] else "sync-video #f")
            if window_settings["sync-video"]:
                os.environ["vblank_mode"] = "0"

        if "show-frame-rate-meter" in window_settings:
            loadPrcFileData("", f"show-frame-rate-meter {window_settings['show-frame-rate-meter']}")

    def enable_vsync(self):
        """Enable VSync in the config."""
        self.config_data["window"]["sync-video"] = True
        os.environ["vblank_mode"] = "1"  # Set this to 0 to enable VSync
        self.save_config()

    def disable_vsync(self):
        """Disable VSync in the config."""
        self.config_data["window"]["sync-video"] = False
        os.environ["vblank_mode"] = "0"
        self.save_config()

    def set_screen_mode(self, mode: str):
        """
        Convenience method to switch screen mode at runtime.

        mode = "windowed", "fullscreen", or "borderless"
        """
        self.config_data["window"]["screen-mode"] = mode
        self.save_config()

    def update_window_position_size(self, x: int, y: int, w: int, h: int):
        """
        Update stored window position/size in the JSON config (for windowed or borderless).
        Called typically after the user moves/resizes the window.
        """
        # If user is in "fullscreen", typically the OS controls the window size/pos.
        screen_mode = self.config_data["window"].get("screen-mode", "windowed")
        if screen_mode != "fullscreen":
            self.config_data["window"]["win-origin"] = [x, y]
            self.config_data["window"]["win-size"] = [w, h]
            self.save_config()
        # If in fullscreen, we typically don't track size/pos changes since there's no real "move."

    def toggle_fullscreen(self):
        """Example method to toggle between fullscreen and windowed."""
        current = self.config_data["window"].get("screen-mode", "windowed")
        if current != "fullscreen":
            self.set_screen_mode("fullscreen")
        else:
            self.set_screen_mode("windowed")
