from typing import Any

from gameplay.condition import Conditions, ResearchCondition
from gameplay.improvement import Improvement
from gameplay.techs.animal_husbandry import AnimalHusbandry
from gameplay.yields import Yields
from managers.i18n import t_


class Pasture(Improvement):
    name = t_("content.improvements.core.resources.pasture.name")
    description = t_("content.improvements.core.resources.pasture.description")
    placeable_on_tiles = True
    tile_yield_improvement = Yields(food=1.0, mode=Yields.ADDITIVE)

    visible_on_condition = True  # Visible from start of the game
    placeable_on_condition = Conditions(ResearchCondition(AnimalHusbandry, None))

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50
