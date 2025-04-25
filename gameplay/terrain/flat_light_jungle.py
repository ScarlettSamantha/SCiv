from typing import Any

from gameplay.improvements.core.resources.farm import Farm
from gameplay.yields import Yields

from ._base_terrain import BaseTerrain


class FlatLightJungle(BaseTerrain):
    _name = "world.terrain.flatland_light_jungle"
    movement_modifier = 0.5
    water_availability = 0
    _model = "assets/models/tiles/flat_light_jungle3.glb"
    _texture = "assets/models/tiles/desert2.png"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Farm)

        self.tile_yield_base = Yields(food=1, culture=1)
