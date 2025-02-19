from data.terrain.hills_desert import HillsDesert as HillsDesertTerrain
from data.tiles.tile import Tile


class HillsDesert(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(HillsDesertTerrain())
