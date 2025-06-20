from typing import Any, Type

from gameplay.terrain.mountain_snow import MountainSnow as MountainSnowTerrain
from gameplay.tile import Tile


class MountainSnow(Tile):
    _terrain: Type[MountainSnowTerrain] = MountainSnowTerrain
    _cache_name = "MountainSnow"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(self._terrain())
