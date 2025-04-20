from typing import Any

from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import t_


class ResearchCenter(Improvement):
    name = t_("content.improvements.core.general.research_center.name")
    description = t_("content.improvements.core.general.research_center.description")
    tile_yield_improvement = Yields(name="research_center", food=1.0, mode=Yields.ADDITIVE)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50
