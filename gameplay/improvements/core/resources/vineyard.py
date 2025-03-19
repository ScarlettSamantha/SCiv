from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import _t


class Vineyard(Improvement):
    name = _t("content.improvements.core.resources.vineyard.name")
    description = _t("content.improvements.core.resources.vineyard.description")
    placeable_on_tiles = True

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(food=1.0, mode=Yields.ADDITIVE)
