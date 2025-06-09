from typing import Any

from gameplay.terrain.flat_desert import FlatDesert
from gameplay.tiles.base_tile import Tile


class LandDesert(Tile):
    _terrain = FlatDesert
    _model = _terrain.model
    _cache_name = "LandDesert"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(self._terrain())
