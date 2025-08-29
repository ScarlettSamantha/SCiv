from typing import Any

from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.yields import Yields
from managers.i18n import T_TranslationOrStrOrNone, t_


class Lake(BaseTerrain):
    _name: T_TranslationOrStrOrNone = t_("world.terrain.lake")
    model_scale: float = 0.41
    _fallback_color = (0, 204, 255)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.fallback_color = self._fallback_color
        self.movement_modifier = 0.5

        self._texture = "lake.png"
        self.tile_yield_base = Yields(food=1)
