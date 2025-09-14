from typing import Any

from gameplay.bits import Bit, DisplayMode
from gameplay.improvements.core.resources.mine import Mine
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import t_


class HillsTundra(BaseTerrain):
    _name = t_("world.terrain.hills_tundra")
    movement_modifier = 0.5
    water_availability = 0.25
    _fallback_color = (186, 186, 186)
    _model = "assets/models/terrain/tundra_hills.glb"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
        self._texture = "hills_tundra.png"

    def register_bits(self) -> None:
        hill = Bit(
            "tundra_hill.glb",
            scale=1.32,
            preferred_slot="center",
            offset=(0.0, 0.0, -0.05),
            hpr=(45.0, 0.0, 0.0),
            display_mode=DisplayMode.OVERRULES_RESOURCE_MODEL.value,
        )
        self.bits.add_bit(hill)
