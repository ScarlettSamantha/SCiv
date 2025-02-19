from data.tiles.tile import Tile
from data.terrain.flat_forest import FlatForest


class LandForest(Tile):
    _terrain = FlatForest
    _model = _terrain.model
    _cache_name = "LandForest"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(self._terrain())
