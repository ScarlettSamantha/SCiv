from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import _t


class MissileSilo(Improvement):
    name = _t("content.improvements.core.military.missile_silo.name")
    description = _t("content.improvements.core.military.missile_silo.description")

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(name="missile_silo", food=1.0, mode=Yields.ADDITIVE)
