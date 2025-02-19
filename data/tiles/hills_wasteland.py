from data.tiles.tile import Tile
from data.terrain.hills_tundra import HillsTundra


class HillsWasteland(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(HillsTundra())
