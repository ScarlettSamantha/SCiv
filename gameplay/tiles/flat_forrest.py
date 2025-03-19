from gameplay.terrain.flat_forest import FlatForest as FlatForestTerrain
from gameplay.tiles.base_tile import BaseTile


class FlatForrest(BaseTile):
    _terrain = FlatForestTerrain
    _model = _terrain.model

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_terrain(FlatForestTerrain())
