from typing import Any

from gameplay.condition import Conditions, ResearchCondition
from gameplay.improvement import Improvement
from gameplay.techs.archery import Archery
from gameplay.yields import Yields
from managers.i18n import t_


class HuntingCamp(Improvement):
    name = t_("content.improvements.core.resources.hunting_camp.name")
    description = t_("content.improvements.core.resources.hunting_camp.description")
    placeable_on_tiles = True
    tile_yield_improvement = Yields(food=1.0, mode=Yields.ADDITIVE)

    placeable_on_condition = Conditions(ResearchCondition(Archery, None))
    visible_on_condition = True  # Visible from start of the game

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50
