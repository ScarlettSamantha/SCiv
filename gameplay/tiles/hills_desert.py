from gameplay.terrain.hills_desert import HillsDesert as HillsDesertTerrain
from gameplay.tiles.base_tile import BaseTile


class HillsDesert(BaseTile):
    _terrain = HillsDesertTerrain
    _model = _terrain.model
    _cache_name = "HillsDesert"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_terrain(HillsDesertTerrain())
