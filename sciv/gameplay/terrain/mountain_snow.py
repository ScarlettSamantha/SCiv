import random
from typing import Any

from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, t_


class MountainSnow(BaseTerrain):
    _name = t_("world.terrain.mountain_snow")
    _fallback_color = (255, 255, 255)
    can_spawn_resources = False
    _model = "assets/models/terrain/mountain_snow.glb"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.movement_modifier = 3
        self.water_availability = 0

        self.passable: bool = False
        self.passable_without_tech: bool = False
        self.enable_random_rotation: bool = True
        self._texture = "mountain_ice.png"

    def random_rotation(self) -> int:
        return (270 + random.randint(0, 5) * 60) % 360

    def model(self) -> T_TranslationOrStr:
        return str(self._model)
