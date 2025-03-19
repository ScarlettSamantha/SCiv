from gameplay.terrain.lake import Lake as LakeTerrain
from gameplay.tiles.base_tile import BaseTile


class Lake(BaseTile):
    _terrain = LakeTerrain
    _model = _terrain.model
    _cache_name = "Lake"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_terrain(LakeTerrain())
