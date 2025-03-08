from managers.i18n import T_TranslationOrStr, T_TranslationOrStrOrNone
from ._base_terrain import BaseTerrain
from ._base_terrain import rgb

from data.terrain.traits.water import open_water_lake


class Lake(BaseTerrain):
    _name: T_TranslationOrStrOrNone = "world.terrain.sea_water"
    _model: T_TranslationOrStr = "assets/models/tiles/water_shallow.glb"
    _texture: T_TranslationOrStr = "assets/models/tiles/water_shallow.png"
    _fallback_color = rgb(0, 119, 255)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fallback_color = self._fallback_color
        self.movement_modifier = 0.5

        self.add_modifiers(open_water_lake)
