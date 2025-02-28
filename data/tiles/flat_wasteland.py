from data.terrain.flat_tundra import FlatTundra
from data.tiles.base_tile import BaseTile


class FlatWasteland(BaseTile):
    _terrain = FlatTundra
    _model = _terrain.model
    _cache_name = "FlatWasteland"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatTundra())
