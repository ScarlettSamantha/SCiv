from typing import Any

from gameplay.terrain.hills_grass import HillsGrass
from gameplay.tile import Tile


class HillsGrassland(Tile):
    _terrrain = HillsGrass
    _model = _terrrain.model
    _cache_name = "HillsGrassland"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(HillsGrass())
