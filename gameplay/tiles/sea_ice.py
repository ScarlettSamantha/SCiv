from data.tiles.base_tile import BaseTile
from data.terrain.sea_ice import SeaIce as SeaIceTerrain
from typing import Type


class SeaIce(BaseTile):
    _terrain: Type[SeaIceTerrain] = SeaIceTerrain
    _model = _terrain._model
    _cache_name = "SeaIce"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(self._terrain())
