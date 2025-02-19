from data.tiles.tile import Tile
from data.terrain.lake import Lake


class Sea(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(Lake())
