from abc import ABC
from typing import TYPE_CHECKING, List, Tuple, Type

from panda3d.core import LRGBColor

from managers.i18n import T_TranslationOrStr, T_TranslationOrStrOrNone

if TYPE_CHECKING:
    from gameplay.improvement import Improvement


def rgb(r: int, g: int, b: int) -> Tuple[float, float, float] | LRGBColor:
    return (r / 255, g / 255, b / 255)


if TYPE_CHECKING:
    from gameplay.tile_modifiers import TileModifier, TileModifiers
    from gameplay.tile_yield_modifier import TileYieldModifier


class BaseTerrain(ABC):
    _name: T_TranslationOrStrOrNone = None
    _model: T_TranslationOrStr = ""
    can_spawn_resources: bool = True

    # This is for things like a forrest, where the terrain is replaced by a new terrain type.
    _warn_user_before_build: bool = False
    _warn_user_before_build_text: T_TranslationOrStr = ""
    _warn_user_before_build_title: T_TranslationOrStr = ""

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

        self._supports_improvements: List[Type["Improvement"]] = []

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

    def supported_improvements(self) -> List[Type["Improvement"]]:
        return self._supports_improvements

    def add_supported_improvement(self, improvement: Type["Improvement"]):
        if improvement not in self._supports_improvements:
            self._supports_improvements.append(improvement)

    def should_warn_user_before_build(self) -> bool:
        return self._warn_user_before_build

    def get_warning_text(self) -> Tuple[T_TranslationOrStr, T_TranslationOrStr]:
        return self._warn_user_before_build_title, self._warn_user_before_build_text

    def on_spawn(self): ...  # meant for runtime decisions like neighbour evaluation when determining yield.

    def on_build_upon(
        self, improvement: "Improvement"
    ): ...  # this is mostly for things like forrests, where the terrain is replaced by a new terrain type.
