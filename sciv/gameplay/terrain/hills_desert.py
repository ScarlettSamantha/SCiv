from typing import Any

from gameplay.improvements.core.resources.mine import Mine
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import t_


class HillsDesert(BaseTerrain):
    _name = t_("world.terrain.hills_desert")
    movement_modifier = 0.5
    water_availability = 0.25
    _fallback_color = (255, 226, 128)
    _model = "assets/models/terrain/hill_desert.glb"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
        self._texture = "hills_desert.png"
