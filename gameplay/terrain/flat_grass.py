from typing import Any

from gameplay.improvements.core.resources.farm import Farm
from gameplay.improvements.core.resources.mine import Mine
from gameplay.improvements.core.resources.pasture import Pasture
from gameplay.yields import Yields

from ._base_terrain import BaseTerrain


class FlatGrass(BaseTerrain):
    _name = "world.terrain.flatland_grass"
    movement_modifier = 0.5
    water_availability = 1
    _model = {0: "assets/models/tiles/grassv2.glb", 50: "assets/models/tiles/grassv3.glb"}
    _fallback_color = (0.0, 0.5, 0.0)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
        self.add_supported_improvement(Farm)
        self.add_supported_improvement(Pasture)
        self._texture = "flat_grass.png"

        self.tile_yield_base = Yields(food=1)
