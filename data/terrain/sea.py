from __future__ import annotations

from gameplay.tile_modifiers import TileModifier, TileModifiers
from gameplay.tile_yield import TileYield
from gameplay.tile_yield_modifier import TileYieldModifier
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

        modifier = TileYieldModifier(TileYield(food=1))
        modifier.add(TileYield(gold=3))
        self.tile_yield_modifiers.add(modifier)
