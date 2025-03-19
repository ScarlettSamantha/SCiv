from gameplay.terrain.flat_ice import FlatIce as FlatIceTerrain
from gameplay.tiles.base_tile import BaseTile


class FlatIce(BaseTile):
    _terrain = FlatIceTerrain
    _model = _terrain.model
    _cache_name = "FlatIce"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_terrain(self._terrain())
