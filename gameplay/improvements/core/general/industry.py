from __future__ import annotations
from gameplay.improvement import Improvement
from gameplay.tile_yield import TileYield
from managers.i18n import _t


class Industry(Improvement):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.improvement.general.industry",
            _t("content.improvements.core.general.industry.name"),
            _t("content.improvements.core.general.industry.description"),
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = TileYield(name="industry", food=1.0, mode=TileYield.ADDITIVE)
