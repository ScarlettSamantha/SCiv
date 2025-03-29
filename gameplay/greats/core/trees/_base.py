from typing import Any
from gameplay.great import GreatsTree


class BaseCoreGreatsTree(GreatsTree):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
