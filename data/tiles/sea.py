from data.tiles.tile import Tile
from data.terrain.sea import Sea as SeaTerrain


class Sea(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(SeaTerrain())
