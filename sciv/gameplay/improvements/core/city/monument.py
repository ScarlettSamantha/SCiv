from typing import Any, Type, TYPE_CHECKING

from gameplay.condition import Condition
from gameplay.improvements.core.city.base_city_improvement import BaseCityImprovement, ImprovementBuildTurnMode
from gameplay.resources.core.basic._base import BasicBaseResource
from gameplay.resources.core.basic.production import Production
from gameplay.yields import Yields
from managers.i18n import t_

if TYPE_CHECKING:
    from gameplay.tile import Tile
    from gameplay.player import Player


class Monument(BaseCityImprovement):
    name = t_("content.improvements.core.city.monument.name")
    description = t_("content.improvements.core.city.monument.description")

    def __init__(self, tile: "Tile", owner: "Player", *args: Any, **kwargs: Any):
        super().__init__(tile=tile, owner=owner, *args, **kwargs)

        self.amount_resource_needed = Yields(production=50)
        self.resource_needed: Type["BasicBaseResource"] = Production

        self.tile_yield_improvement = Yields(culture=1)  # just unlocks the ability to train units.
        self.conditions.add(condition=Condition.no_condition())  # no-op, we can build this at the start of the game.
        self.maintenance_cost = Yields(gold=0.5)

        self.upgradable = True

        self.multi_turn_mode = ImprovementBuildTurnMode.MULTI_TURN_RESOURCE
