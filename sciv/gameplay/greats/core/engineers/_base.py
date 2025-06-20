from typing import Any

from gameplay.greats.core._base import CoreGreat


class CoreBaseGreatEngineer(CoreGreat):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
