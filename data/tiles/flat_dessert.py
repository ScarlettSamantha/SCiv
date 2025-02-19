from data.terrain.flat_desert import FlatDessert as FlatDesertTerrain
from data.tiles.tile import Tile


class FlatDesert(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatDesertTerrain())
