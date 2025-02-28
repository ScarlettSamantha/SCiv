from data.terrain.flat_desert import FlatDessert as FlatDesertTerrain
from data.tiles.base_tile import BaseTile


class FlatDesert(BaseTile):
    _terrain = FlatDesertTerrain
    _model = _terrain.model
    _cache_name = "FlatDesert"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatDesertTerrain())
