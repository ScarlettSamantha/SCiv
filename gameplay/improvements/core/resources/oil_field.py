from __future__ import annotations

from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import _t


class OilField(Improvement):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.improvement.resource.oil_field",
            _t("content.improvements.core.resource.oil_field.name"),
            _t("content.improvements.core.resource.oil_field.description"),
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(name="oil_field", food=1.0, mode=Yields.ADDITIVE)
