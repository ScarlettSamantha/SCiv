from data.terrain.coast import Coast as CoastTerrain
from data.tiles.tile import Tile


class Coast(Tile):
    _cache_name = "Coast"
    _terrain = CoastTerrain()
    _model = _terrain.model

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(self._terrain)
