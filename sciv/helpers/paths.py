from helpers.windows import WindowsHelper
from helpers.linux import LinuxHelper


class PathsHelper:
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
