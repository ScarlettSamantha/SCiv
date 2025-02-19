from data.tiles.tile import Tile
from data.terrain.hills_snow import HillsSnow as HillSnowTerrain


class HillsSnow(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(HillSnowTerrain())
