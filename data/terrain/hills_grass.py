from ._base_terrain import BaseTerrain
from data.terrain.traits.land import buildable_flat_land


class HillsGrass(BaseTerrain):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = "world.terrain.hills_gras"

        self.movement_modifier = 0.75
        self.water_availability = 0.75

        self._model = "assets/models/tiles/hills_grass.obj"
        self._texture = "assets/models/tiles/hills_grass.png"

        self.add_modifiers(buildable_flat_land)
