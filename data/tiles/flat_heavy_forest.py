from data.terrain.flat_heavy_forest import FlatHeavyForest as FlatHeavyForestTerrain
from data.tiles.tile import Tile


class FlatHeavyForest(Tile):
    _terrain = FlatHeavyForestTerrain
    _model = _terrain.model

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatHeavyForestTerrain())
