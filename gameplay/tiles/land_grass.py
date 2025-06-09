from typing import Any

from gameplay.terrain.flat_grass import FlatGrass
from gameplay.tiles.base_tile import Tile


class LandGrass(Tile):
    _terrain = FlatGrass
    _model = _terrain.model
    _cache_name = "LandGrass"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(self._terrain())
