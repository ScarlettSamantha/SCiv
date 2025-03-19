from typing import Type

from gameplay.terrain.sea import Sea
from gameplay.tiles.base_tile import BaseTile


class SeaWater(BaseTile):
    _terrain: Type[Sea] = Sea
    _model = _terrain._model
    _cache_name = "SeaWater"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_terrain(self._terrain())
