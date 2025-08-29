from typing import Any

from gameplay.improvements.core.resources.farm import Farm
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.yields import Yields
from managers.i18n import t_


class FlatLightJungle(BaseTerrain):
    _name = t_("world.terrain.flatland_light_jungle")
    movement_modifier = 0.5
    water_availability = 0
    _fallback_color = (91, 128, 64)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Farm)

        self.tile_yield_base = Yields(food=1, culture=1)
        self._texture = "flat_light_jungle.png"
