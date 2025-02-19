from data.terrain.flat_grass import FlatGrass as FlatGrassTerrain
from data.tiles.tile import Tile


class FlatGrass(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatGrassTerrain())
