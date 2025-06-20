from typing import Any, Type

from gameplay.terrain.sea import Sea
from gameplay.tile import Tile


class SeaWater(Tile):
    _terrain: Type[Sea] = Sea
    _model = _terrain.get_model()
    _cache_name = "SeaWater"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(self._terrain())
