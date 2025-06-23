from pathlib import Path
from typing import Optional
from system.vars import APPLICATION_NAME


class LinuxHelper:
    cache_dir: Optional[str] = None
    config_dir: Optional[str] = None
    data_dir: Optional[str] = None

    @classmethod
    def get_cache_dir(cls) -> str:
        if cls.cache_dir is not None:
            return cls.cache_dir

        from xdg import xdg_cache_home  # type: ignore

        cache_dir = str(xdg_cache_home() / APPLICATION_NAME.lower())  # type: ignore

        Path(cache_dir).mkdir(parents=True, exist_ok=True)

        cls.cache_dir = cache_dir

        return cache_dir

    @classmethod
    def get_config_dir(cls) -> str:
        if cls.config_dir is not None:
            return cls.config_dir

        from xdg import xdg_config_home  # type: ignore

        config_dir = str(xdg_config_home() / APPLICATION_NAME.lower())  # type: ignore

        Path(config_dir).mkdir(parents=True, exist_ok=True)

        cls.config_dir = config_dir

        return config_dir

    @classmethod
    def get_data_dir(cls) -> str:
        if cls.data_dir is not None:
            return cls.data_dir

        from xdg import xdg_data_home  # type: ignore

        data_dir = str(xdg_data_home() / APPLICATION_NAME.lower())  # type: ignore

        Path(data_dir).mkdir(parents=True, exist_ok=True)

        cls.data_dir = data_dir

        return data_dir
