from typing import Any

from gameplay.condition import Conditions, ResearchCondition
from gameplay.improvement import Improvement
from gameplay.techs.sailing import Sailing
from gameplay.yields import Yields
from managers.i18n import t_


class FishingBoats(Improvement):
    name = t_("content.improvements.core.resources.fishing_boats.name")
    description = t_("content.improvements.core.resources.fishing_boats.description")
    placeable_on_tiles = True

    visible_condition = Conditions(ResearchCondition(Sailing, None))
    placeable_on_condition = Conditions(ResearchCondition(Sailing, None))

    placeable_by_player = True

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(food=1.0, mode=Yields.ADDITIVE)
