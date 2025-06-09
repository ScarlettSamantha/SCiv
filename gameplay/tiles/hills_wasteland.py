from typing import Any

from gameplay.terrain.hills_tundra import HillsTundra
from gameplay.tile import Tile


class HillsWasteland(Tile):
    _terrain = HillsTundra
    _model = _terrain.model
    _cache_name = "HillsWasteland"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(HillsTundra())
