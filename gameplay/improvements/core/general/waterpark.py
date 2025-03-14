from __future__ import annotations

from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import _t


class Waterpark(Improvement):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.improvement.general.waterpark",
            _t("content.improvements.core.general.waterpark.name"),
            _t("content.improvements.core.general.waterpark.description"),
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(name="waterpark", food=1.0, mode=Yields.ADDITIVE)
