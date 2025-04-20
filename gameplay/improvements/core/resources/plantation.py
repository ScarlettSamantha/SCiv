from typing import Any

from gameplay.condition import Conditions, ResearchCondition
from gameplay.improvement import Improvement
from gameplay.techs.steel import Steel
from gameplay.yields import Yields
from managers.i18n import t_


class Plantation(Improvement):
    name = t_("content.improvements.core.resources.plantation.name")
    description = t_("content.improvements.core.resources.plantation.description")
    placeable_on_tiles = True

    visible_on_condition = Conditions(
        ResearchCondition(Steel, None)
    )  # Steel because machetes are needed to clear jungle
    placeable_on_condition = Conditions(ResearchCondition(Steel, None))

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(food=1.0, mode=Yields.ADDITIVE)
