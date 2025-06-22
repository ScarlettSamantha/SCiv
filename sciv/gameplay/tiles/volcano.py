from typing import Any

from gameplay.terrain.volcano import Volcano as VolcanoTerrain
from gameplay.tile import Tile


class Volcano(Tile):
    _terrain = VolcanoTerrain
    _model = _terrain.model
    _cache_name = "Volcano"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(self._terrain())
