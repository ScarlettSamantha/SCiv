from __future__ import annotations

from gameplay.tile_yield import TileYield
from gameplay.tile_yield_modifier import TileYieldModifier
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

        modifier = TileYieldModifier(TileYield(food=1))
        modifier.add(TileYield(gold=3))
        self.tile_yield_modifiers.add(modifier)
