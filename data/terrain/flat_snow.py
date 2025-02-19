from ._base_terrain import BaseTerrain

from data.terrain.traits.land import buildable_flat_land


class FlatSnow(BaseTerrain):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = "world.terrain.flatland_grass"

        self.movement_modifier = 1
        self.water_availability = 0.25

        self._model = "assets/models/tiles/grass2.obj"
        self._texture = "assets/models/tiles/grass2.png"

        self.add_modifiers(buildable_flat_land)
