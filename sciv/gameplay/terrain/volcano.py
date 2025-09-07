from typing import Any

from gameplay.bits import Bit
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.yields import Yields
from managers.i18n import t_


class Volcano(BaseTerrain):
    _name = t_("world.terrain.volcano")

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
        volcano = Bit(
            model="volcano.glb",
            scale=1.3,
            hpr=(-75, 0, 0),
            offset=(0, 0, 0.0),
            blocks_resource_model_spawning=True,
            preferred_slot="center",
        )
        self.bits.add_bit(volcano)
