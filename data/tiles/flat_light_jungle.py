from data.terrain.flat_light_jungle import FlatLightJungle as FlatLightJungleTerrain
from data.tiles.tile import Tile


class FlatLightJungle(Tile):
    _terrain = FlatLightJungleTerrain
    _model = _terrain.model
    _cache_name = "FlatLightJungle"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatLightJungleTerrain())
