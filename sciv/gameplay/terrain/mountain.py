from typing import Any

from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import t_


class Mountain(BaseTerrain):
    _name = t_("world.terrain.mountain")
    _fallback_color = 112, 83, 15
    can_spawn_resources = False
    _model = "assets/models/terrain/mountain.glb"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.movement_modifier = 3
        self.water_availability = 0

        self.passable: bool = False
        self.passable_without_tech: bool = False
        self._texture = "mountain_dirt.png"
