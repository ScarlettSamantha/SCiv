from gameplay.yields import Yields
from managers.i18n import T_TranslationOrStr

from ._base_terrain import BaseTerrain, rgb


class Sea(BaseTerrain):
    _name = "world.terrain.sea_water"
    _model = "assets/models/tiles/water_deep.glb"
    _texture: T_TranslationOrStr = "assets/models/tiles/town.png"
    _fallback_color = rgb(0, 119, 255)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = "world.terrain.sea_water"
        self.movement_modifier = 0.5

        self.passable: bool = False
        self.passable_without_tech: bool = False

        self.tile_yield_base.add(Yields(food=1, gold=1))
