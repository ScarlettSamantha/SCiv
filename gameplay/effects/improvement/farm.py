from typing import Any

from gameplay.yields import Yields
from system.effects import Effect


class FarmEffect(Effect):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.yield_impact = Yields(food=3, mode=Yields.ADDITIVE)
