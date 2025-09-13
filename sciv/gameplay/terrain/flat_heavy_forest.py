from typing import Any

from gameplay.bits import Bit
from gameplay.improvements.core.resources.farm import Farm
from gameplay.improvements.core.resources.logging_camp import LoggingCamp
from gameplay.improvements.core.resources.mine import Mine
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.yields import Yields
from managers.i18n import t_


class FlatHeavyForest(BaseTerrain):
    _name = t_("world.terrain.flatland_heavy_forest")
    movement_modifier = 0.5
    _model = "assets/models/terrain/flat_forest.glb"
    water_availability = 0.75
    _fallback_color = (91, 128, 64)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
        self.add_supported_improvement(Farm)
        self.add_supported_improvement(LoggingCamp)

        self.tile_yield_base = Yields(production=1)

        self._texture = "flat_heavy_forest.png"

    def register_bits(self) -> None:
        forest = Bit(
            "flat_heavy_forest.glb", scale=1.65, preferred_slot="center", offset=(0.0, 0.0, -0.05), hpr=(45.0, 0.0, 0.0)
        )
        self.bits.add_bit(forest)
