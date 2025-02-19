from __future__ import annotations
from ._base_terrain import BaseTerrain

from world.terrain.traits.land import buildable_flat_land


class FlatForest(BaseTerrain):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = "world.terrain.flatland_forest"

        self.movement_modifier = 0.5
        self.water_availability = 0.75

        self._model = "assets/models/tiles/forrest3.obj"
        self._texture = "assets/models/tiles/forrest3.png"

        self.add_modifiers(buildable_flat_land)
