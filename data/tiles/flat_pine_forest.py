from data.terrain.flat_pine_forest import FlatPineForest as FlatPineForestTerrain
from data.tiles.tile import Tile


class FlatPineForest(Tile):
    _terrain = FlatPineForestTerrain
    _model = _terrain.model

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatPineForestTerrain())
