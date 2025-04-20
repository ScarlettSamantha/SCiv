from typing import Any

from gameplay.condition import Conditions, ResearchCondition
from gameplay.improvement import Improvement
from gameplay.techs import electricity
from gameplay.techs.combustion import Combustion
from gameplay.yields import Yields
from managers.i18n import t_


class PowerPlantOil(Improvement):
    name = t_("content.improvements.core.resources.power_plant_oil.name")
    description = t_("content.improvements.core.resources.power_plant_oil.description")
    placeable_on_tiles = True

    visible_on_condition = Conditions(
        ResearchCondition(electricity.Electricity, None), ResearchCondition(Combustion, None)
    )
    placeable_on_condition = Conditions(
        ResearchCondition(electricity.Electricity, None), ResearchCondition(Combustion, None)
    )

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(food=1.0, mode=Yields.ADDITIVE)
