from typing import Any

from exceptions._base_exception import BaseException


class ConfigException(BaseException):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)


class ConfigEntryNotFound(ConfigException):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
