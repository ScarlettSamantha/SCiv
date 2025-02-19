from data.tiles.tile import Tile
from data.terrain.sea import Sea as SeaTerrain


class Sea(Tile):
    _terrain = SeaTerrain
    _model = _terrain._model
    _cache_name = "sea"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(terrain=self._terrain())
