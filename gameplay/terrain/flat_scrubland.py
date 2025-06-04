from typing import Any

from gameplay.improvements.core.resources.mine import Mine
from gameplay.yields import Yields

from ._base_terrain import BaseTerrain


class FlatScrubland(BaseTerrain):
    _name = "world.terrain.flatland_scrubland"
    movement_modifier = 0.5
    water_availability = 0.75

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)

        self.tile_yield_base = Yields(food=1)
        self._texture = "flat_scrubland.png"
