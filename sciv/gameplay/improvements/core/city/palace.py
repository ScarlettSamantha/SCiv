from typing import TYPE_CHECKING, Any, Type

from gameplay.improvements.core.city.base_city_improvement import BaseCityImprovement
from gameplay.resources.core.basic._base import BasicBaseResource
from gameplay.resources.core.basic.production import Production
from gameplay.yields import Yields
from managers.i18n import t_

if TYPE_CHECKING:
    from gameplay.tile import Tile
    from gameplay.player import Player


class Palace(BaseCityImprovement):
    name = t_("content.improvements.core.city.palace.name")
    description = t_("content.improvements.core.city.palace.description")
    _model = "cities/palace_stage_1.glb"
    _model_scale = 0.30
    _model_preferred_slot = "palace"
    placeable_on_city = True
    placeable_on_condition = True

    def __init__(self, tile: "Tile", owner: "Player", *args: Any, **kwargs: Any):
        super().__init__(tile=tile, owner=owner, *args, **kwargs)

        self.amount_resource_needed = Yields(production=50)
        self.resource_needed: Type["BasicBaseResource"] = Production

        self.tile_yield_improvement = Yields(gold=5, production=2, food=2, science=2, culture=2, faith=2)
