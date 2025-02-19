from data.tiles.tile import Tile
from data.terrain.flat_grass import FlatGrass


class LandGrass(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatGrass())
