from typing import Any
from gameplay.terrain.flat_heavy_forest import FlatHeavyForest as FlatHeavyForestTerrain
from gameplay.tiles.base_tile import BaseTile


class FlatHeavyForest(BaseTile):
    _terrain = FlatHeavyForestTerrain
    _model = _terrain.model

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(FlatHeavyForestTerrain())
