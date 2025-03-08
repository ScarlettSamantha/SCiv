from data.tiles.base_tile import BaseTile
from data.terrain.mountain import Mountain as MountainTerrain
from typing import Type

from managers.i18n import T_TranslationOrStr


class Mountain(BaseTile):
    _terrain: Type[MountainTerrain] = MountainTerrain
    _model: T_TranslationOrStr = _terrain._model
    _cache_name = "Mountain"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(self._terrain())
