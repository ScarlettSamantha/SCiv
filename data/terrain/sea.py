from __future__ import annotations

from managers.i18n import T_TranslationOrStr
from ._base_terrain import BaseTerrain
from ._base_terrain import rgb


from data.terrain.traits.water import open_water_sea


class Sea(BaseTerrain):
    _name = "world.terrain.sea_water"
    _model = "assets/models/tiles/water_deep.glb"
    _texture: T_TranslationOrStr = "assets/models/tiles/town.png"
    _fallback_color = rgb(0, 119, 255)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = "world.terrain.sea_water"
        self.movement_modifier = 0.5

        self.add_modifiers(open_water_sea)
