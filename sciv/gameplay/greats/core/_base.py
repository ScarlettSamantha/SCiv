from typing import Any
from gameplay.great import Great
from gameplay.resources.core.basic.gold import Gold


class CoreGreat(Great):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(resource_type_required=Gold(), *args, **kwargs)
