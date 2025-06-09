from typing import Any
from gameplay.terrain.coast import Coast as CoastTerrain
from gameplay.tile import Tile
from helpers.colors import Colors


class Coast(Tile):
    _cache_name = "Coast"
    _terrain = CoastTerrain()
    _model = _terrain.model
    _fallback_color = Colors.TIEL

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(self._terrain)
