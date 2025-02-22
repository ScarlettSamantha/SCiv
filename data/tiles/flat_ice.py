from data.terrain.flat_ice import FlatIce as FlatIceTerrain
from data.tiles.tile import Tile


class FlatIce(Tile):
    _terrain = FlatIceTerrain
    _model = _terrain.model
    _cache_name = "FlatIce"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(self._terrain())
