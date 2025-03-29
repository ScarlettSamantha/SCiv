from typing import Any

from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import t_


class NationalPark(Improvement):
    name = t_("content.improvements.core.general.national_park.name")
    description = t_("content.improvements.core.general.national_park.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(name="national_park", food=1.0, mode=Yields.ADDITIVE)
