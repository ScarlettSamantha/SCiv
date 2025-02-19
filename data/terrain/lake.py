from ._base_terrain import BaseTerrain
from ._base_terrain import rgb

from data.terrain.traits.water import open_water_lake


class Lake(BaseTerrain):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = "world.terrain.sea_water"
        self.fallback_color = rgb(0, 119, 255)
        self.movement_modifier = 0.5
        self._model = "assets/models/tiles/sea.obj"
        self._texture = "assets/models/tiles/sea_water.png"

        self.add_modifiers(open_water_lake)
