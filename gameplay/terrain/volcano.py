from typing import Any
from gameplay.bits import Bit
from gameplay.yields import Yields

from ._base_terrain import BaseTerrain


class Volcano(BaseTerrain):
    _name = "world.terrain.volcano"

    _fallback_color = (0, 119, 255)

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
                scale=1.0,
                hpr=(0, 0, 0),
                offset=(0, 0, 0),
            )
        )

        return super().register_bits()
