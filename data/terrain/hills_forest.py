from ._base_terrain import BaseTerrain
from data.terrain.traits.land import buildable_flat_land


class HillsForest(BaseTerrain):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = "world.terrain.hills_forest"

        self.movement_modifier = 0.5
        self.water_availability = 0.5

        self._model = "assets/models/tiles/grass2.obj"
        self._texture = "assets/models/tiles/grass2.png"

        self.add_modifiers(buildable_flat_land)
