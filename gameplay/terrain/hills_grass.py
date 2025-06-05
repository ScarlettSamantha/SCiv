from typing import Any

from gameplay.improvements.core.resources.mine import Mine
from gameplay.yields import Yields

from ._base_terrain import BaseTerrain


class HillsGrass(BaseTerrain):
    _name = "world.terrain.hills_grass"
    movement_modifier = 0.75
    water_availability = 0.75
    _fallback_color = (54, 109, 16)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
        self._texture = "hills_grass.png"
        self.tile_yield_base = Yields(production=1)
