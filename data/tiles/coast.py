from data.terrain.coast import Coast as CoastTerrain
from data.tiles.tile import Tile


class Coast(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(CoastTerrain())
