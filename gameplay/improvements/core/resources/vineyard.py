from __future__ import annotations

from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import _t


class Vineyard(Improvement):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.improvement.resource.vineyard",
            _t("content.improvements.core.resource.vineyard.name"),
            _t("content.improvements.core.resource.vineyard.description"),
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(name="vineyard", food=1.0, mode=Yields.ADDITIVE)
