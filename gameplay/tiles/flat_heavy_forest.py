from data.terrain.flat_heavy_forest import FlatHeavyForest as FlatHeavyForestTerrain
from data.tiles.base_tile import BaseTile


class FlatHeavyForest(BaseTile):
    _terrain = FlatHeavyForestTerrain
    _model = _terrain.model

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatHeavyForestTerrain())
