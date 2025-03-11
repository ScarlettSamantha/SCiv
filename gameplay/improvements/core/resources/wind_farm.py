from __future__ import annotations

from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import _t


class WindFarm(Improvement):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.improvement.resource.wind_farm",
            _t("content.improvements.core.resource.wind_farm.name"),
            _t("content.improvements.core.resource.wind_farm.description"),
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(name="wind_farm", food=1.0, mode=Yields.ADDITIVE)
