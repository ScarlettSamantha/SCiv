from typing import Any

from gameplay.terrain.sea import Sea as SeaTerrain
from gameplay.tiles.base_tile import BaseTile


class Sea(BaseTile):
    _terrain = SeaTerrain
    _model = _terrain.get_model()
    _cache_name = "sea"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(terrain=self._terrain())
