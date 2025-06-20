from random import uniform
from typing import Any

from gameplay.bits import Bit
from gameplay.improvements.core.resources.logging_camp import LoggingCamp
from gameplay.yields import Yields

from ._base_terrain import BaseTerrain


class FlatPineForest(BaseTerrain):
    _name = "world.terrain.flat_pine_forest"
    movement_modifier = 0.5
    water_availability = 0.75
    _fallback_color = (27, 64, 0)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(LoggingCamp)

        self.tile_yield_base = Yields(production=1)
        self._texture = "flat_pine_forest.png"

    def register_bits(self) -> None:
        self.bits.add_bit(
            Bit(
                model="tree_heavy_forest.glb",
                scale=uniform(0.8, 0.95),
                preferred_slot="center",
                disabled=False,
                id="tree_pine_forest_combined",
                default_lighting=False,
                offset=(0, 0, -0.3),
                hpr=(uniform(-180, 180), 0, 0),
            )
        )
