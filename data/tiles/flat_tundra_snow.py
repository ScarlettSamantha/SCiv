from data.terrain.flat_tundra_snow import FlatTundraSnow as FlatTundraSnowTerrain
from data.tiles.tile import Tile


class FlatTundraSnow(Tile):
    _terrain = FlatTundraSnowTerrain
    _model = _terrain.model
    _cache_name = "FlatTundraSnow"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(self._terrain())
