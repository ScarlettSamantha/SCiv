from typing import Any

from gameplay.bits import Bit
from gameplay.improvements.core.resources.logging_camp import LoggingCamp
from gameplay.improvements.core.resources.mine import Mine
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import t_


class HillsForest(BaseTerrain):
    _name = t_("world.terrain.hills_forest")
    movement_modifier = 0.5
    water_availability = 0.5
    _fallback_color = (91, 128, 64)
    _model = "assets/models/terrain/hill_forest.glb"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
        self.add_supported_improvement(LoggingCamp)
        self._texture = "hills_forest.png"

    def register_bits(self) -> None:
        hill = Bit(
            "forest_hill.glb", scale=1.30, preferred_slot="center", offset=(0.0, 0.0, -0.05), hpr=(45.0, 0.0, 0.0)
        )
        self.bits.add_bit(hill)
