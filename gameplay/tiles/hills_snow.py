from typing import Any

from gameplay.terrain.hills_snow import HillsSnow as HillSnowTerrain
from gameplay.tiles.base_tile import BaseTile


class HillsSnow(BaseTile):
    _model = HillSnowTerrain.model
    _cache_name = "HillsSnow"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(HillSnowTerrain())
