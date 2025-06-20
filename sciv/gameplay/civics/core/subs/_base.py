from typing import Any

from gameplay.civic import CivicSubtree


class BaseCoreSubtree(CivicSubtree):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
