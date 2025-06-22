from typing import Any
from gameplay.bits import Bit
from gameplay.yields import Yields

from ._base_terrain import BaseTerrain


class Volcano(BaseTerrain):
    _name = "world.terrain.volcano"

    _fallback_color = (30, 0, 0)  # Dark red color for volcano

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.name = "world.terrain.volcano"
        self.movement_modifier = 0.5

        self.passable: bool = False
        self.passable_without_tech: bool = False

        self.tile_yield_base.add(Yields.nullYield())
        self._texture = "volcano.png"

    def register_bits(self) -> None:
        self.bits.add_bit(
            Bit(
                model="volcano.glb",
                scale=1.3,
                hpr=(-75, 0, 0),
                offset=(0, 0, 0),
                default_lighting=False,
                default_shader=False,
                blocks_resource_model_spawning=True,
                preferred_slot="center",
            )
        )

        return super().register_bits()
