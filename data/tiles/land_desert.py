from data.tiles.tile import Tile
from data.terrain.flat_desert import FlatDessert


class LandDesert(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatDessert())
