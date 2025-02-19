from __future__ import annotations

from managers.i18n import T_TranslationOrStr
from ._base_terrain import BaseTerrain
from ._base_terrain import rgb

from data.terrain.traits.land import mountain


class Mountain(BaseTerrain):
    _name = "world.terrain.mountain"
    _model = "assets/models/tiles/mountain.glb"
    _texture: T_TranslationOrStr = "assets/models/tiles/mountain.png"
    _fallback_color = rgb(0, 119, 255)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.movement_modifier = 3
        self.water_availability = 0

        self.add_modifiers(mountain)
