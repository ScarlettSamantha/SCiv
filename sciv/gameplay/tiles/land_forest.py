from typing import Any

from gameplay.terrain.flat_forest import FlatForest
from gameplay.tile import Tile


class LandForest(Tile):
    _terrain = FlatForest
    _model = _terrain.model
    _cache_name = "LandForest"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(self._terrain())
