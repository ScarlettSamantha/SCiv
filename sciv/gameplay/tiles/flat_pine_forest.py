from typing import Any

from gameplay.terrain.flat_pine_forest import FlatPineForest as FlatPineForestTerrain
from gameplay.tile import Tile


class FlatPineForest(Tile):
    _terrain = FlatPineForestTerrain
    _model = _terrain.model

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(FlatPineForestTerrain())
