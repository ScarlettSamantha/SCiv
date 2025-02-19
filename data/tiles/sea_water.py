from data.tiles.tile import Tile
from data.terrain.sea import Sea
from typing import Type


class SeaWater(Tile):
    _terrain: Type[Sea] = Sea
    _model = _terrain._model
    _cache_name = "SeaWater"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(self._terrain())
