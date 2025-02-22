from data.terrain.flat_tundra import FlatTundra
from data.tiles.tile import Tile


class FlatWasteland(Tile):
    _terrain = FlatTundra
    _model = _terrain.model
    _cache_name = "FlatWasteland"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatTundra())
