from typing import Any


from ._base_terrain import BaseTerrain


class Mountain(BaseTerrain):
    _name = "world.terrain.mountain"
    _fallback_color = 112, 83, 15
    can_spawn_resources = False

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.movement_modifier = 3
        self.water_availability = 0

        self.passable: bool = False
        self.passable_without_tech: bool = False
        self._texture = "mountain_dirt.png"
