from typing import Any

from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.yields import Yields
from managers.i18n import t_


class Coast(BaseTerrain):
    _name = t_("world.terrain.coast")
    fallback_color = (0, 119, 255)
    movement_modifier = 0.5
    _model = "assets/models/terrain/coast.glb"
    model_pos_z_offset = -0.41

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.passable: bool = False
        self.passable_without_tech: bool = False
        self._texture = "coast.png"

        self.tile_yield_base = Yields(food=1)
