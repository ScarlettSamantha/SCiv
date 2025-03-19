from gameplay.improvements.core.resources.mine import Mine

from ._base_terrain import BaseTerrain


class FlatScrubland(BaseTerrain):
    _name = "world.terrain.flatland_scrubland"
    movement_modifier = 0.5
    water_availability = 0.75
    _model = "assets/models/tiles/flat_scrubland.glb"
    _texture = "assets/models/tiles/forrest3.png"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
