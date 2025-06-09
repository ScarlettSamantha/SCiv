from typing import Any
from gameplay.terrain.flat_desert import FlatDesert as FlatDesertTerrain
from gameplay.tiles.base_tile import Tile


class FlatDesert(Tile):
    _terrain = FlatDesertTerrain
    _model = _terrain.model
    _cache_name = "FlatDesert"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(FlatDesertTerrain())
