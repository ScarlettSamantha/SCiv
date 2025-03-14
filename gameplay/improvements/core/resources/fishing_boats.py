from __future__ import annotations

from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import _t


class FishingBoats(Improvement):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.improvement.resource.fishing_boats",
            _t("content.improvements.core.resource.fishing_boats.name"),
            _t("content.improvements.core.resource.fishing_boats.description"),
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(name="fishing_boats", food=1.0, mode=Yields.ADDITIVE)
