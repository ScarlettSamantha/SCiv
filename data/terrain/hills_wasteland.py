# Lake class
from managers.i18n import T_TranslationOrStr
from ._base_terrain import BaseTerrain, rgb
from data.terrain.traits.water import open_water_lake


class Lake(BaseTerrain):
    _name: T_TranslationOrStr = "world.terrain.sea_water"
    _model: str = "assets/models/tiles/sea.obj"
    _texture: T_TranslationOrStr = "assets/models/tiles/sea_water.png"
    _fallback_color = rgb(0, 119, 255)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = self._name
        self.fallback_color = self._fallback_color
        self.movement_modifier = 0.5

        self.add_modifiers(open_water_lake)
