import re
from os import PathLike, name
from typing import Optional


class WindowsHelper:
    _is_windows: Optional[bool] = None

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
