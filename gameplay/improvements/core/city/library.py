from typing import TYPE_CHECKING, Any, Type

from gameplay.condition import ResearchCondition
from gameplay.improvements.core.city.base_city_improvement import BaseCityImprovement, ImprovementBuildTurnMode
from gameplay.resources.core.basic._base import BasicBaseResource
from gameplay.resources.core.basic.production import Production

from gameplay.yields import Yields
from managers.i18n import t_

if TYPE_CHECKING:
    from gameplay.tile import Tile
    from gameplay.player import Player


class Library(BaseCityImprovement):
    name = t_("content.improvements.core.city.library.name")
    description = t_("content.improvements.core.city.library.description")
    _model = ""

    def __init__(self, tile: "Tile", player: "Player", *args: Any, **kwargs: Any):
        from gameplay.techs.writing import Writing

        super().__init__(tile=tile, player=player, *args, **kwargs)

        self.amount_resource_needed = Yields(production=8)
        self.resource_needed: Type["BasicBaseResource"] = Production

        self.tile_yield_improvement = Yields(Science=2)
        self.conditions.add(condition=ResearchCondition(Writing))
        self.maintenance_cost = Yields(gold=1.0)

        self.upgradable = True

        self.multi_turn_mode = ImprovementBuildTurnMode.MULTI_TURN_RESOURCE
