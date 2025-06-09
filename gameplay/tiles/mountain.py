from typing import Any, Type

from gameplay.terrain.mountain import Mountain as MountainTerrain
from gameplay.tiles.base_tile import Tile


class Mountain(Tile):
    _terrain: Type[MountainTerrain] = MountainTerrain
    _cache_name = "Mountain"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(self._terrain())
