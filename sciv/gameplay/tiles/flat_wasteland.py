from typing import Any

from gameplay.terrain.flat_tundra import FlatTundra
from gameplay.tile import Tile


class FlatWasteland(Tile):
    _terrain = FlatTundra
    _model = _terrain.model
    _cache_name = "FlatWasteland"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(FlatTundra())
