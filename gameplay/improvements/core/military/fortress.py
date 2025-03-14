from __future__ import annotations

from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import _t
from managers.tags import Tag


class Fortress(Improvement):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.improvement.military.fortress",
            _t("content.improvements.core.military.fortress.name"),
            _t("content.improvements.core.military.fortress.description"),
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(name="military_base", food=1.0, mode=Yields.ADDITIVE)

        self.tags = self.add_tag(Tag("builder", self))
