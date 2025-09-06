from typing import Any, Type

from gameplay.terrain.sea import Sea
from gameplay.tile import Tile
from managers.i18n import t_


class SeaWater(Tile):
    name = t_("world.terrain.sea_water")
    _terrain: Type[Sea] = Sea
    _model = _terrain.get_model()
    _cache_name = "SeaWater"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(self._terrain())
