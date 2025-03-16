# Lake class
from gameplay.improvements.core.resources.mine import Mine
from managers.i18n import T_TranslationOrStr, T_TranslationOrStrOrNone

from ._base_terrain import BaseTerrain, rgb


class Lake(BaseTerrain):
    _name: T_TranslationOrStrOrNone = "world.terrain.sea_water"
    _model: T_TranslationOrStr = "assets/models/tiles/wasteland.glb"
    _texture: T_TranslationOrStr = "assets/models/tiles/sea_water.png"
    _fallback_color = rgb(0, 119, 255)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fallback_color = self._fallback_color
        self.movement_modifier = 0.5

        self.add_supported_improvement(Mine)
