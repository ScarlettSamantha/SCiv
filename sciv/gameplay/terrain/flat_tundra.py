from typing import Any

from gameplay.improvements.core.resources.mine import Mine
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import t_


class FlatTundra(BaseTerrain):
    _name = t_("world.terrain.flatland_tundra")
    movement_modifier = 1
    water_availability = 0.25
    _fallback_color = (238, 238, 238)
    _model = "assets/models/terrain/tundra_flat.glb"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
        self._texture = "flat_tundra.png"
