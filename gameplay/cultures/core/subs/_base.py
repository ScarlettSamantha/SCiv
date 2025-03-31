from typing import Any
from gameplay.culture import CultureSubtree


class BaseCoreSubtree(CultureSubtree):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
