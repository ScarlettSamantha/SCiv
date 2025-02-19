from data.terrain.flat_snow import FlatSnow as FlatSnowTerrain
from data.tiles.tile import Tile


class FlatSnow(Tile):
    _terrain = FlatSnowTerrain
    _model = _terrain.model
    _cache_name = "FlatSnow"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatSnowTerrain())
