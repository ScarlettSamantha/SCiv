from gameplay.terrain.flat_desert import FlatDesert as FlatDesertTerrain
from gameplay.tiles.base_tile import BaseTile


class FlatDesert(BaseTile):
    _terrain = FlatDesertTerrain
    _model = _terrain.model
    _cache_name = "FlatDesert"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_terrain(FlatDesertTerrain())
