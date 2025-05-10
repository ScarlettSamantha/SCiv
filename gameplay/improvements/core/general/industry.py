from typing import Any

from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import t_


class Industry(Improvement):
    name = t_("content.improvements.core.general.industry.name")
    description = t_("content.improvements.core.general.industry.description")
    tile_yield_improvement = Yields(name="industry", food=1.0, mode=Yields.ADDITIVE)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
