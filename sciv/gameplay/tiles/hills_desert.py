from typing import Any

from gameplay.terrain.hills_desert import HillsDesert as HillsDesertTerrain
from gameplay.tile import Tile


class HillsDesert(Tile):
    _terrain = HillsDesertTerrain
    _model = _terrain.model
    _cache_name = "HillsDesert"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(HillsDesertTerrain())
