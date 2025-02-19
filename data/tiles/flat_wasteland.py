from data.terrain.flat_tundra import FlatTundra
from data.tiles.tile import Tile


class FlatWasateland(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatTundra())
