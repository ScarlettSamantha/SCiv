from typing import Any

from gameplay.condition import Conditions, ResearchCondition
from gameplay.improvement import Improvement
from gameplay.techs.electricity import Electricity
from gameplay.yields import Yields
from managers.i18n import t_


class PowerPlantCoal(Improvement):
    name = t_("content.improvements.core.resources.power_plant_coal.name")
    description = t_("content.improvements.core.resources.power_plant_coal.description")
    placeable_on_tiles = True
    tile_yield_improvement = Yields(food=1.0, mode=Yields.ADDITIVE)

    visible_on_condition = Conditions(ResearchCondition(Electricity, None))
    placeable_on_condition = Conditions(ResearchCondition(Electricity, None))

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
