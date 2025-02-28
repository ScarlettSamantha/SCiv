from data.tiles.base_tile import BaseTile
from data.terrain.flat_desert import FlatDessert


class LandDesert(BaseTile):
    _terrain = FlatDessert
    _model = _terrain.model
    _cache_name = "LandDesert"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(self._terrain())
