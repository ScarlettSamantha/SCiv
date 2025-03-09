from gameplay.terrain.traits.land import buildable_flat_land

from ._base_terrain import BaseTerrain


class FlatDessert(BaseTerrain):
    _name = "world.terrain.flatland_dessert"
    movement_modifier = 0.5
    water_availability = 0
    _model = "assets/models/tiles/dessert.glb"
    _texture = "assets/models/tiles/dessert2.png"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_modifiers(buildable_flat_land)
