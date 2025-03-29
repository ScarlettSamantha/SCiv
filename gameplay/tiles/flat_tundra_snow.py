from typing import Any

from gameplay.terrain.flat_tundra_snow import FlatTundraSnow as FlatTundraSnowTerrain
from gameplay.tiles.base_tile import BaseTile


class FlatTundraSnow(BaseTile):
    _model = FlatTundraSnowTerrain.model
    _cache_name = "FlatTundraSnow"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(FlatTundraSnowTerrain())
