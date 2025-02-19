from __future__ import annotations
from ._base_terrain import BaseTerrain


class Coast(BaseTerrain):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = "world.terrain.coast"
        self.fallback_color = (0, 119, 255)
        self.movement_modifier = 0.5
        self._model = "assets/models/tiles/water2.obj"
        self._texture = "assets/models/tiles/water2.png"
        self._model = None
