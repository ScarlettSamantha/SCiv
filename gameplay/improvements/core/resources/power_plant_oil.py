from __future__ import annotations

from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import _t


class PowerPlantOil(Improvement):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.improvement.resource.power_plant_oil",
            _t("content.improvements.core.resource.power_plant_oil.name"),
            _t("content.improvements.core.resource.power_plant_oil.description"),
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(name="power_plant_oil", food=1.0, mode=Yields.ADDITIVE)
