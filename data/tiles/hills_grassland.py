from data.tiles.tile import Tile
from data.terrain.hills_grass import HillsGrass


class HillsGrassland(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(HillsGrass())
