from data.tiles.tile import Tile
from data.terrain.hills_tundra import HillsTundra


class HillsWasteland(Tile):
    _terrain = HillsTundra
    _model = _terrain.model
    _cache_name = "HillsWasteland"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(HillsTundra())
