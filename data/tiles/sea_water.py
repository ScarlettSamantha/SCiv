from data.tiles.tile import Tile
from data.terrain.sea import Sea


class SeaWater(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(Sea())
