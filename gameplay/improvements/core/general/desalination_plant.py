from __future__ import annotations

from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import _t


class DesalinationPlant(Improvement):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.improvement.general.desalination_plant",
            _t("content.improvements.core.general.desalination_plant.name"),
            _t("content.improvements.core.general.desalination_plant.description"),
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(name="desalination_plant", food=1.0, mode=Yields.ADDITIVE)
