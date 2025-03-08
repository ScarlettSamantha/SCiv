from data.terrain.flat_pine_forest import FlatPineForest as FlatPineForestTerrain
from data.tiles.base_tile import BaseTile


class FlatPineForest(BaseTile):
    _terrain = FlatPineForestTerrain
    _model = _terrain.model

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatPineForestTerrain())
