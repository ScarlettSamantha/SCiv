from typing import Any

from gameplay.terrain.hills_forest import HillsForest as HillsForestTerrain
from gameplay.tile import Tile


class HillsForest(Tile):
    _terrain = HillsForestTerrain
    _model = _terrain.model
    _cache_name = "HillsForest"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(HillsForestTerrain())
