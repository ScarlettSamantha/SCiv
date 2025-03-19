from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import _t


class Plantation(Improvement):
    name = _t("content.improvements.core.resources.plantation.name")
    description = _t("content.improvements.core.resources.plantation.description")
    placeable_on_tiles = True

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(food=1.0, mode=Yields.ADDITIVE)
