from typing import Any
from gameplay.terrain.flat_jungle import FlatJungle as FlatJungleTerrain
from gameplay.tiles.base_tile import Tile


class FlatJungle(Tile):
    _terrain = FlatJungleTerrain
    _model = _terrain.model
    _cache_name = "FlatJungle"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(FlatJungleTerrain())
