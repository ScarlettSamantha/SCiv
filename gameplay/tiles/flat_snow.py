from typing import Any

from gameplay.terrain.flat_snow import FlatSnow as FlatSnowTerrain
from gameplay.tiles.base_tile import Tile


class FlatSnow(Tile):
    _terrain = FlatSnowTerrain
    _model = _terrain.model
    _cache_name = "FlatSnow"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(FlatSnowTerrain())
