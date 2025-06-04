from typing import Any

from managers.i18n import T_TranslationOrStr

from ._base_terrain import BaseTerrain


class Mountain(BaseTerrain):
    _name = "world.terrain.mountain"
    _fallback_color = 0, 119, 255
    can_spawn_resources = False
    model_height = 0.25

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.movement_modifier = 3
        self.water_availability = 0

        self.passable: bool = False
        self.passable_without_tech: bool = False
        self._texture = "mountain_dirt.png"

    def model(self) -> T_TranslationOrStr:
        return str(self._model)
