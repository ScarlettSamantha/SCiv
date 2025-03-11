from typing import Type

from gameplay.condition import Condition
from gameplay.improvements.core.city.base_city_improvement import BaseCityImprovement, ImprovementBuildTurnMode
from gameplay.resources.core.basic._base import BasicBaseResource
from gameplay.resources.core.basic.production import Production
from gameplay.tile_yield import TileYield
from managers.i18n import t_


class Monument(BaseCityImprovement):
    name = t_("content.improvements.core.city.monument.name")
    description = t_("content.improvements.core.city.monument.description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.amount_resource_needed = TileYield(production=50)
        self.resource_needed: Type["BasicBaseResource"] = Production

        self.tile_yield_improvement = TileYield(culture=1)  # just unlocks the ability to train units.
        self.conditions.add(condition=Condition.no_condition())  # no-op, we can build this at the start of the game.
        self.maintenance_cost = TileYield(gold=0.5)

        self.upgradable = True

        self.multi_turn_mode = ImprovementBuildTurnMode.MULTI_TURN_RESOURCE
