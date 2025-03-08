from data.tiles.base_tile import BaseTile
from data.terrain.sea import Sea
from typing import Type


class SeaWater(BaseTile):
    _terrain: Type[Sea] = Sea
    _model = _terrain._model
    _cache_name = "SeaWater"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(self._terrain())
