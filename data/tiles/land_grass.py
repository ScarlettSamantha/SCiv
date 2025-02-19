from data.tiles.tile import Tile
from data.terrain.flat_grass import FlatGrass


class LandGrass(Tile):
    _terrain = FlatGrass
    _model = _terrain.model
    _cache_name = "LandGrass"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(self._terrain())
