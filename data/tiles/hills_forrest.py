from data.terrain.hills_forest import HillsForest as HillsForestTerrain
from data.tiles.base_tile import BaseTile


class HillsForest(BaseTile):
    _terrain = HillsForestTerrain
    _model = _terrain.model
    _cache_name = "HillsForest"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(HillsForestTerrain())
