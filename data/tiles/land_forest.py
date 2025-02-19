from data.tiles.tile import Tile
from data.terrain.flat_forest import FlatForest


class LandForest(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatForest())
