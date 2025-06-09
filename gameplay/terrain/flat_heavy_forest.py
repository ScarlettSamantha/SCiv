from typing import Any

from gameplay.bits import Bit
from gameplay.improvements.core.resources.farm import Farm
from gameplay.improvements.core.resources.logging_camp import LoggingCamp
from gameplay.improvements.core.resources.mine import Mine
from gameplay.yields import Yields
from ._base_terrain import BaseTerrain


class FlatHeavyForest(BaseTerrain):
    _name = "world.terrain.flat_heavy_forest"
    movement_modifier = 0.5
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
        self.bits.add_bit(
            Bit(
                model="tree_forest_combined.glb",
                scale=2.0,
                preferred_slot="center",
                disabled=True,
                id="tree_forest_combined",
            )
        )
