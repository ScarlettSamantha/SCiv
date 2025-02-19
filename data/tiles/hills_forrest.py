from data.terrain.hills_forest import HillsForest as HillsForestTerrain
from data.tiles.tile import Tile


class HillsForest(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(HillsForestTerrain())
