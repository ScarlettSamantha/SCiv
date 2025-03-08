from gameplay.terrain.hills_tundra import HillsTundra as HillsTundraTerrain
from gameplay.tiles.base_tile import BaseTile


class HillsTundra(BaseTile):
    _cache_name = "HillsTundra"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(HillsTundraTerrain())
