from typing import TYPE_CHECKING, List, Tuple

from panda3d.core import LRGBColor

from managers.i18n import T_TranslationOrStr, T_TranslationOrStrOrNone


def rgb(r: int, g: int, b: int) -> Tuple[float, float, float] | LRGBColor:
    return (r / 255, g / 255, b / 255)


if TYPE_CHECKING:
    from gameplay.tile_modifiers import TileModifier, TileModifiers
    from gameplay.tile_yield_modifier import TileYieldModifier


class BaseTerrain:
    _name: T_TranslationOrStrOrNone = None
    _model: T_TranslationOrStr = ""
    can_spawn_resources: bool = True

    def __init__(self):
        from gameplay.tile_modifiers import TileModifiers
        from gameplay.tile_yield_modifier import TileYieldModifier

        self.fallback_color: LRGBColor | Tuple[float, float, float] = rgb(225, 0, 255)

        self.name: T_TranslationOrStr = "" if self._name is None else self._name
        self.user_title: T_TranslationOrStr = ""
        self._texture: T_TranslationOrStr = ""

        self.movement_modifier: float = 0.0
        self.water_availability: float = 1.0
        self.radatiation: float = 0.0

        self.tile_modifiers: TileModifiers = TileModifiers()
        self.tile_yield_modifiers: TileYieldModifier = TileYieldModifier()

        self.passable: bool = True
        self.passable_without_tech: bool = True

    def model(self) -> T_TranslationOrStr:
        return str(self._model)

    def texture(self) -> T_TranslationOrStr:
        return self._texture

    def add_modifiers(self, modifiers: List["TileModifier"] | Tuple["TileModifier", ...]):
        for item in modifiers:
            self.tile_modifiers.append(item)

    def add_modifier(self, modifier: "TileModifier"):
        self.tile_modifiers.append(modifier)

    def add_tile_yield_modifier(self, tile_yield_modifier: "TileYieldModifier", auto_calculate: bool = True):
        self.tile_yield_modifiers.add(tile_yield_modifier)
        if auto_calculate:
            tile_yield_modifier.calculate()

    def get_modifiers(self) -> "TileModifiers":
        return self.tile_modifiers

    def color(self) -> LRGBColor | Tuple[float, float, float]:
        return self.fallback_color
