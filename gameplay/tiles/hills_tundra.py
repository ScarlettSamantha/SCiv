from data.tiles.base_tile import BaseTile
from data.terrain.hills_tundra import HillsTundra as HillsTundraTerrain


class HillsTundra(BaseTile):
    _cache_name = "HillsTundra"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(HillsTundraTerrain())
