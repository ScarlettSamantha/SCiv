from __future__ import annotations

from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import _t


class Pasture(Improvement):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.improvement.resource.pasture",
            _t("content.improvements.core.resource.pasture.name"),
            _t("content.improvements.core.resource.pasture.description"),
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(name="pasture", food=1.0, mode=Yields.ADDITIVE)
