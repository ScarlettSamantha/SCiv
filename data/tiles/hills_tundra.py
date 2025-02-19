from data.tiles.tile import Tile
from data.terrain.hills_tundra import HillsTundra as HillsTundraTerrain


class HillsTundra(Tile):
    _cache_name = "HillsTundra"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(HillsTundraTerrain())
