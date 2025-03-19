from gameplay.yields import Yields
from system.effects import Effect


class FarmEffect(Effect):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.yield_impact = Yields(food=2, mode=Yields.ADDITIVE)
