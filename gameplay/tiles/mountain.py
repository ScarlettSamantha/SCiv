from typing import Type

from gameplay.terrain.mountain import Mountain as MountainTerrain
from gameplay.tiles.base_tile import BaseTile
from managers.i18n import T_TranslationOrStr


class Mountain(BaseTile):
    _terrain: Type[MountainTerrain] = MountainTerrain
    _model: T_TranslationOrStr = _terrain._model
    _cache_name = "Mountain"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_terrain(self._terrain())
