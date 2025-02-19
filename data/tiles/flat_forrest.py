from data.terrain.flat_forest import FlatForest as FlatForestTerrain
from data.tiles.tile import Tile


class FlatForrest(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatForestTerrain())
