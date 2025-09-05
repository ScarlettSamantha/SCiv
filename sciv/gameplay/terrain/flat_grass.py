from typing import Any

from gameplay.improvements.core.resources.farm import Farm
from gameplay.improvements.core.resources.mine import Mine
from gameplay.improvements.core.resources.pasture import Pasture
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.yields import Yields
from managers.i18n import t_


class FlatGrass(BaseTerrain):
    _name = t_("world.terrain.flatland_grass")
    movement_modifier = 0.5
    water_availability = 1
    _fallback_color = (106, 255, 0)
    _model = "assets/models/terrain/flat_grassland.glb"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
        self.add_supported_improvement(Farm)
        self.add_supported_improvement(Pasture)
        self._texture = "flat_grass.png"

        self.tile_yield_base = Yields(food=1)

    def register_bits(self) -> None:
        pass
