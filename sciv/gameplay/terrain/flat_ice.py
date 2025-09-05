from typing import Any

from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import t_


class FlatIce(BaseTerrain):
    _name = t_("world.terrain.flatland_ice")
    movement_modifier = 1
    water_availability = 0.25
    _fallback_color = (255, 255, 255)
    _model = "assets/models/terrain/flat_iceland.glb"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._texture = "flat_ice.png"
