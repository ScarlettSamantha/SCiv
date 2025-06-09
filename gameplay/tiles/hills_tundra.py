from typing import Any

from gameplay.terrain.hills_tundra import HillsTundra as HillsTundraTerrain
from gameplay.tiles.base_tile import Tile


class HillsTundra(Tile):
    _model = HillsTundraTerrain.model
    _cache_name = "HillsTundra"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(HillsTundraTerrain())
