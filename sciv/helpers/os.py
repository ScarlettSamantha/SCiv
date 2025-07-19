import re
from abc import abstractmethod
from os import PathLike, name
from pathlib import Path
from subprocess import CompletedProcess
from typing import Optional

from system.vars import APPLICATION_NAME


class AbstractOsHelper:
    DATA_DIR: str = "data"
    CONFIG_DIR: str = "config"
    CACHE_DIR: str = "cache"
    DEBUG_DIR: str = "debug"

    @classmethod
    @abstractmethod
    def get_cache_dir(cls) -> str: ...

    @classmethod
    @abstractmethod
    def get_config_dir(cls) -> str: ...

    @classmethod
    @abstractmethod
    def get_data_dir(cls) -> str: ...

    @classmethod
    @abstractmethod
    def get_debug_dir(cls) -> str: ...


class LinuxHelper(AbstractOsHelper):
    cache_dir: Optional[str] = None
    config_dir: Optional[str] = None
    data_dir: Optional[str] = None

    @classmethod
    def get_cache_dir(cls) -> str:
        if cls.cache_dir is not None:
            return cls.cache_dir

        from xdg import (
            xdg_cache_home,  # type: ignore Leave this here as the type ignore is for the server not the client.
        )

        cache_dir = str(xdg_cache_home() / APPLICATION_NAME.lower())  # type: ignore
        Path(cache_dir).mkdir(parents=True, exist_ok=True)

        cls.cache_dir = cache_dir

        return cache_dir

    @classmethod
    def get_config_dir(cls) -> str:
        if cls.config_dir is not None:
            return cls.config_dir

        from xdg import (
            xdg_config_home,  # type: ignore Leave this here as the type ignore is for the server not the client.
        )

        config_dir = str(xdg_config_home() / APPLICATION_NAME.lower())  # type: ignore

        Path(config_dir).mkdir(parents=True, exist_ok=True)

        cls.config_dir = config_dir

        return config_dir

    @classmethod
    def get_data_dir(cls) -> str:
        if cls.data_dir is not None:
            return cls.data_dir

        from xdg import (
            xdg_data_home,  # type: ignore Leave this here as the type ignore is for the server not the client.
        )

        data_dir = str(xdg_data_home() / APPLICATION_NAME.lower())  # type: ignore

        Path(data_dir).mkdir(parents=True, exist_ok=True)

        cls.data_dir = data_dir

        return data_dir

    @classmethod
    def get_debug_dir(cls) -> str:
        debug_dir: Path = Path(cls.get_data_dir()) / cls.DEBUG_DIR
        debug_dir.mkdir(parents=True, exist_ok=True)
        return str(debug_dir)

    @classmethod
    def open_folder(cls, folder: str) -> None:
        import subprocess  # nosec

        try:
            subprocess.run(["xdg-open", folder], check=True)  # nosec
        except subprocess.CalledProcessError as e:
            print(f"Failed to open folder {folder}: {e}")


class WindowsHelper(AbstractOsHelper):
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
        cache_dir: Path = cls.get_windows_local_path() / cls.CACHE_DIR
        cache_dir.mkdir(parents=True, exist_ok=True)
        cls.cache_dir = str(cache_dir)
        return str(cache_dir)

    @classmethod
    def get_config_dir(cls) -> str:
        if cls.config_dir is not None:
            return cls.config_dir
        config_dir: Path = cls.get_windows_local_path() / cls.CONFIG_DIR
        config_dir.mkdir(parents=True, exist_ok=True)
        cls.config_dir = str(config_dir)
        return str(config_dir)

    @classmethod
    def get_data_dir(cls) -> str:
        if cls.data_dir is not None:
            return cls.data_dir
        data_dir: Path = cls.get_windows_local_path() / cls.DATA_DIR
        data_dir.mkdir(parents=True, exist_ok=True)
        cls.data_dir = str(data_dir)
        return str(data_dir)

    @classmethod
    def get_debug_dir(cls) -> str:
        debug_dir = cls.get_windows_local_path() / cls.DEBUG_DIR
        debug_dir.mkdir(parents=True, exist_ok=True)
        return str(debug_dir)

    @classmethod
    def open_folder(cls, path: str) -> bool:
        import subprocess  # nosec

        process: CompletedProcess[bytes] = subprocess.run(["explorer", path], check=True)  # nosec

        if process.returncode != 0:
            return False
        return True
