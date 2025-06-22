from typing import Any

from gameplay.terrain.lake import Lake as LakeTerrain
from gameplay.tile import Tile


class Lake(Tile):
    _terrain = LakeTerrain
    _model = _terrain.model
    _cache_name = "Lake"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(LakeTerrain())
