from typing import Any

from gameplay.terrain.sea_ice import SeaIce as SeaIceTerrain
from gameplay.tile import Tile


class SeaIce(Tile):
    _model = SeaIceTerrain.get_model()
    _cache_name = "SeaIce"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(SeaIceTerrain())
