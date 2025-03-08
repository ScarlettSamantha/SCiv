from data.tiles.base_tile import BaseTile
from data.terrain.hills_tundra import HillsTundra


class HillsWasteland(BaseTile):
    _terrain = HillsTundra
    _model = _terrain.model
    _cache_name = "HillsWasteland"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(HillsTundra())
