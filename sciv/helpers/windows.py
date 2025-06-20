import re
from os import PathLike
from typing import Optional


class WindowsHelper:
    _is_windows: Optional[bool] = None

    @classmethod
    def is_windows(cls) -> bool:
        """Check if the current operating system is Windows."""
        if cls._is_windows is None:
            cls._is_windows = re.match(r"^win", str(__import__("os").name), re.IGNORECASE) is not None
        return cls._is_windows

    @staticmethod
    def win32_to_unix_path(path: str | PathLike[str]) -> str:
        return re.sub(r"^([a-zA-Z]):", r"/\1", str(path).replace("\\", "/"))
