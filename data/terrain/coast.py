from __future__ import annotations
from ._base_terrain import BaseTerrain



from panda3d.core import Texture

from terrain.traits.water import open_water_coast

class Coast(BaseTerrain):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = 'world.terrain.coast'
        self.fallback_color = rgb(0, 119, 255)
        self.movement_modifier = 0.5
        self._model = "openciv/assets/models/tiles/water2.obj"
        self._texture = texture("openciv/assets/models/tiles/water2.png")
        self._model = None

