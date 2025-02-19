from __future__ import annotations
from ._base_terrain import BaseTerrain

from ursina import Texture
from world.terrain.traits.land import buildable_flat_land


class FlatDessert(BaseTerrain):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = "world.terrain.flatland_dessert"

        self.movement_modifier = 0.5
        self.water_availability = 0

        self._model = "assets/models/tiles/dessert2.obj"
        self._texture = Texture("assets/models/tiles/dessert2.png")

        self.add_modifiers(buildable_flat_land)
