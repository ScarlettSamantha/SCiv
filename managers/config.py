import json
import os
from panda3d.core import loadPrcFileData
from panda3d.core import ClockObject


class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config_data = self._load_config()

    def _load_config(self):
        """Internal method: load config from JSON or return default if missing/invalid."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Failed to parse {self.config_file}: {e}")

        # If not found or failed, return a reasonable default:
        return {
            "render": {"clock-mode": "limited", "clock-frame-rate": 60},
            "window": {
                "screen-mode": "windowed",  # "windowed", "fullscreen", or "borderless"
                "win-origin": [100, 100],
                "win-size": [1280, 720],
                "window-title": "My Panda3D App",
            },
        }

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
            loadPrcFileData("", f"sync-video {bool(window_settings['sync-video'])}")

        if "show-frame-rate-meter" in window_settings:
            loadPrcFileData("", f"show-frame-rate-meter {window_settings['show-frame-rate-meter']}")

    def set_screen_mode(self, mode):
        """
        Convenience method to switch screen mode at runtime.
        mode = "windowed", "fullscreen", or "borderless"
        """
        self.config_data["window"]["screen-mode"] = mode
        self.save_config()

    def update_window_position_size(self, x, y, w, h):
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
