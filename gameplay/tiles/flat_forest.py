from typing import Any
from gameplay.terrain.flat_forest import FlatForest as FlatForestTerrain
from gameplay.tile import Tile


class FlatForest(Tile):
    _terrain = FlatForestTerrain
    _model = _terrain.model

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(FlatForestTerrain())
