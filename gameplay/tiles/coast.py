from typing import Any
from gameplay.terrain.coast import Coast as CoastTerrain
from gameplay.tiles.base_tile import BaseTile


class Coast(BaseTile):
    _cache_name = "Coast"
    _terrain = CoastTerrain()
    _model = _terrain.model

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(self._terrain)
