from typing import Any, Type

from gameplay.terrain.mountain_snow import MountainSnow as MountainSnowTerrain
from gameplay.tiles.base_tile import BaseTile
from managers.i18n import T_TranslationOrStr


class MountainSnow(BaseTile):
    _terrain: Type[MountainSnowTerrain] = MountainSnowTerrain
    _model: T_TranslationOrStr = _terrain._model
    _cache_name = "MountainSnow"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(self._terrain())
