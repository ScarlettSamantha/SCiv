from gameplay.terrain.flat_forest import FlatForest
from gameplay.tiles.base_tile import BaseTile


class LandForest(BaseTile):
    _terrain = FlatForest
    _model = _terrain.model
    _cache_name = "LandForest"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_terrain(self._terrain())
