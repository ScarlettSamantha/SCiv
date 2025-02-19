from __future__ import annotations
from typing import List, Tuple
from gameplay.tile_modifiers import TileModifiers, TileModifier
from gameplay.tile_yield_modifier import TileYieldModifier
from managers.i18n import T_TranslationOrStr
from panda3d.core import LRGBColor


def rgb(r: int, g: int, b: int) -> Tuple[float, float, float] | LRGBColor:
    return (r / 255, g / 255, b / 255)


class BaseTerrain:
    def __init__(self):
        self.fallback_color: LRGBColor | Tuple[float, float, float] = rgb(225, 0, 255)

        self.name: T_TranslationOrStr = ""
        self.user_title: T_TranslationOrStr = ""
        self._texture: T_TranslationOrStr = ""
        self._model = "assets/models/tiles/base_testing.obj"

        self.movement_modifier: float = 0.0
        self.water_availability: float = 1.0
        self.radatiation: float = 0.0

        self.tile_modifiers: TileModifiers = TileModifiers()
        self.tile_yield_modifiers: List[TileYieldModifier] = []

    def model(self):
        return self.model

    def texture(self):
        return self._texture

    def add_modifiers(self, modifiers: List[TileModifier] | Tuple[TileModifier, ...]):
        for item in modifiers:
            self.tile_modifiers.append(item)

    def add_tile_yield_modifier(self, tile_yield_modifier: TileYieldModifier):
        self.tile_yield_modifiers.append(tile_yield_modifier)

    def get_modifiers(self) -> TileModifiers:
        return self.tile_modifiers

    def color(self) -> LRGBColor | Tuple[float, float, float]:
        return self.fallback_color
