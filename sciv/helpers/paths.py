from pathlib import Path

from helpers.os import LinuxHelper, WindowsHelper


class PathsHelper:
    base_path: str = str(Path(__file__).parent.parent.resolve())

    @classmethod
    def get_cache_dir(cls) -> str:
        if WindowsHelper.is_windows():
            return WindowsHelper.get_cache_dir()
        else:
            return LinuxHelper.get_cache_dir()

    @classmethod
    def get_config_dir(cls) -> str:
        if WindowsHelper.is_windows():
            return WindowsHelper.get_config_dir()
        else:
            return LinuxHelper.get_config_dir()

    @classmethod
    def get_data_dir(cls) -> str:
        if WindowsHelper.is_windows():
            return WindowsHelper.get_data_dir()
        else:
            return LinuxHelper.get_data_dir()

    @classmethod
    def open_folder(cls, folder: str):
        if WindowsHelper.is_windows():
            WindowsHelper.open_folder(folder)
        else:
            LinuxHelper.open_folder(folder)

    @classmethod
    def get_debug_dir(cls) -> str:
        if WindowsHelper.is_windows():
            return WindowsHelper.get_debug_dir()
        else:
            return LinuxHelper.get_debug_dir()

    @classmethod
    def get_base_path(cls) -> Path:
        return Path(cls.base_path)

    @classmethod
    def get_gameplay_dir(cls) -> Path:
        return cls.get_base_path() / "gameplay"

    @classmethod
    def get_actions_dir(cls) -> Path:
        return cls.get_gameplay_dir() / "actions"

    @classmethod
    def get_assets_dir(cls) -> Path:
        return cls.get_base_path() / "assets"

    @classmethod
    def get_terrain_dir(cls) -> Path:
        return cls.get_gameplay_dir() / "terrain"
