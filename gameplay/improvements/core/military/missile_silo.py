from typing import Any

from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import t_


class MissileSilo(Improvement):
    name = t_("content.improvements.core.military.missile_silo.name")
    description = t_("content.improvements.core.military.missile_silo.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

        self.tile_yield_improvement = Yields(name="missile_silo", food=1.0, mode=Yields.ADDITIVE)
