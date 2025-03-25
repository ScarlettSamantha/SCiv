from gameplay.terrain.sea_ice import SeaIce as SeaIceTerrain
from gameplay.tiles.base_tile import BaseTile


class SeaIce(BaseTile):
    _model = SeaIceTerrain._model
    _cache_name = "SeaIce"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_terrain(SeaIceTerrain())
