from __future__ import annotations

from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import _t


class HuntingCamp(Improvement):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.improvement.resource.hunting_camp",
            _t("content.improvements.core.resource.hunting_camp.name"),
            _t("content.improvements.core.resource.hunting_camp.description"),
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(name="hunting_camp", food=1.0, mode=Yields.ADDITIVE)
