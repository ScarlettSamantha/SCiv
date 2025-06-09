from typing import Any

from gameplay.terrain.flat_tundra_snow import FlatTundraSnow as FlatTundraSnowTerrain
from gameplay.tiles.base_tile import Tile


class FlatTundraSnow(Tile):
    _model = FlatTundraSnowTerrain.model
    _cache_name = "FlatTundraSnow"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(FlatTundraSnowTerrain())
