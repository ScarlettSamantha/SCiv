from gameplay.terrain.mountain import Mountain as MountainTerrain
from gameplay.tiles.base_tile import BaseTile


class Mountain(BaseTile):
    _terrain = MountainTerrain
    _model = _terrain._model
    _cache_name = "Mountain"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(self._terrain())
