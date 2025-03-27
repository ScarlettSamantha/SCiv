from typing import Type

from gameplay.condition import Condition
from gameplay.improvements.core.city.base_city_improvement import BaseCityImprovement, ImprovementBuildTurnMode
from gameplay.resources.core.basic._base import BasicBaseResource
from gameplay.resources.core.basic.production import Production
from gameplay.yields import Yields
from managers.i18n import t_


class Barracks(BaseCityImprovement):
    name = t_("content.improvements.core.city.barracks.name")
    description = t_("content.improvements.core.city.barracks.description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.amount_resource_needed = Yields(production=8)
        self.resource_needed: Type["BasicBaseResource"] = Production

        self.tile_yield_improvement = Yields.nullYield()  # just unlocks the ability to train units.
        self.conditions.add(condition=Condition.no_condition())  # no-op, we can build this at the start of the game.
        self.maintenance_cost = Yields(gold=0.5)

        self.upgradable = True

        self.multi_turn_mode = ImprovementBuildTurnMode.MULTI_TURN_RESOURCE
