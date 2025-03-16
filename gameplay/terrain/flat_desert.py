from gameplay.improvements.core.resources.mine import Mine

from ._base_terrain import BaseTerrain


class FlatDessert(BaseTerrain):
    _name = "world.terrain.flatland_dessert"
    movement_modifier = 0.5
    water_availability = 0
    _model = "assets/models/tiles/dessert.glb"
    _texture = "assets/models/tiles/dessert2.png"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_supported_improvement(Mine)
