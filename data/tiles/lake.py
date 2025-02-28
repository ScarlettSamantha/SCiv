from data.tiles.base_tile import BaseTile
from data.terrain.lake import Lake as LakeTerrain


class Lake(BaseTile):
    _terrain = LakeTerrain
    _model = _terrain.model
    _cache_name = "Lake"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(LakeTerrain())
