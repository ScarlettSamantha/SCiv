from typing import Any

from gameplay.improvements.core.resources.mine import Mine
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.yields import Yields
from managers.i18n import t_


class HillsSnow(BaseTerrain):
    _name = t_("world.terrain.hills_snow")

    movement_modifier = 0.5
    water_availability = 0.25
    _fallback_color = (238, 238, 238)
    _model = "assets/models/terrain/hill_snow.glb"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)

        self.tile_yield_base = Yields(production=1)
        self._texture = "hills_snow.png"
