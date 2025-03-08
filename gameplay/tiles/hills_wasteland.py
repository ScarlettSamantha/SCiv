from gameplay.terrain.hills_tundra import HillsTundra
from gameplay.tiles.base_tile import BaseTile


class HillsWasteland(BaseTile):
    _terrain = HillsTundra
    _model = _terrain.model
    _cache_name = "HillsWasteland"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(HillsTundra())
