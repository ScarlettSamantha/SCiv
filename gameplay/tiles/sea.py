from data.tiles.base_tile import BaseTile
from data.terrain.sea import Sea as SeaTerrain


class Sea(BaseTile):
    _terrain = SeaTerrain
    _model = _terrain._model
    _cache_name = "sea"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(terrain=self._terrain())
