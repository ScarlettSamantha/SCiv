from data.tiles.base_tile import BaseTile
from data.terrain.mountain_snow import MountainSnow as MountainSnowTerrain
from typing import Type

from managers.i18n import T_TranslationOrStr


class MountainSnow(BaseTile):
    _terrain: Type[MountainSnowTerrain] = MountainSnowTerrain
    _model: T_TranslationOrStr = _terrain._model
    _cache_name = "MountainSnow"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(self._terrain())
