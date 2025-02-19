from data.tiles.tile import Tile
from data.terrain.mountain import Mountain as MountainTerrain


class Mountain(Tile):
    _terrain = MountainTerrain
    _model = _terrain._model
    _cache_name = "Mountain"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(self._terrain())
