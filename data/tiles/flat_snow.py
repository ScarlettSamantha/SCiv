from data.terrain.flat_snow import FlatSnow as FlatSnowTerrain
from data.tiles.tile import Tile


class FlatSnow(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatSnowTerrain())
