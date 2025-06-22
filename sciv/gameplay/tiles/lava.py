from typing import Any

from gameplay.terrain.mountain import Mountain as MountainTerrain
from gameplay.tile import Tile


class Mountain(Tile):
    _terrain = MountainTerrain
    _model = _terrain.get_model()
    _cache_name = "Mountain"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(self._terrain())
