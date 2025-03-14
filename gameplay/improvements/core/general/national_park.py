from __future__ import annotations

from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import _t


class NationalPark(Improvement):
    def __init__(self, *args, **kwargs):
        super().__init__(
            "core.improvement.general.national_park",
            _t("content.improvements.core.general.national_park.name"),
            _t("content.improvements.core.general.national_park.description"),
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(name="national_park", food=1.0, mode=Yields.ADDITIVE)
