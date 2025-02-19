from data.terrain.flat_forest import FlatForest as FlatForestTerrain
from data.tiles.tile import Tile


class FlatForrest(Tile):
    _terrain = FlatForestTerrain
    _model = _terrain.model

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatForestTerrain())
