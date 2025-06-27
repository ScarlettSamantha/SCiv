import re
from os import PathLike, name
from typing import Optional
from system.vars import APPLICATION_NAME
from pathlib import Path


class WindowsHelper:
    _is_windows: Optional[bool] = None
    cache_dir: Optional[str] = None
    config_dir: Optional[str] = None
    data_dir: Optional[str] = None

    @classmethod
    def load_dll(cls, dll_name: str) -> None:
        if cls.is_windows():
            try:
                import ctypes  # type: ignore

                ctypes.CDLL(dll_name)
            except OSError as e:
                raise RuntimeError(f"Failed to load DLL '{dll_name}': {e}")

    @classmethod
    def is_windows(cls) -> bool:
        """Check if the current operating system is Windows."""
        if cls._is_windows is None:
            cls._is_windows = name != "posix"
        return cls._is_windows

    @staticmethod
    def win32_to_unix_path(path: str | PathLike[str]) -> str:
        return re.sub(r"^([a-zA-Z]):", lambda match: f"/{match.group(1).lower()}", str(path).replace("\\", "/"))

    @staticmethod
    def unix_to_win32_path(path: str | PathLike[str]) -> str:
        path = str(path).replace("\\", "/")
        return re.sub(r"^/([a-z])", lambda match: f"{match.group(1).upper()}:/", path)

    @classmethod
    def get_windows_local_path(cls) -> Path:
        return Path.home() / "AppData" / "Local" / APPLICATION_NAME.lower()

    @classmethod
    def get_cache_dir(cls) -> str:
        if cls.cache_dir is not None:
            return cls.cache_dir
        cache_dir = cls.get_windows_local_path() / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cls.cache_dir = str(cache_dir)
        return str(cache_dir)

    @classmethod
    def get_config_dir(cls) -> str:
        if cls.config_dir is not None:
            return cls.config_dir
        config_dir = cls.get_windows_local_path() / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        cls.config_dir = str(config_dir)
        return str(config_dir)

    @classmethod
    def get_data_dir(cls) -> str:
        if cls.data_dir is not None:
            return cls.data_dir
        data_dir = cls.get_windows_local_path() / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        cls.data_dir = str(data_dir)
        return str(data_dir)

    @classmethod
    def open_folder(cls, path: str) -> bool:
        import subprocess  # nosec

        process = subprocess.run(["explorer", path], check=True)  # nosec

        if process.returncode != 0:
            return False
        return True
