from abc import ABC
import random
from typing import TYPE_CHECKING, Callable, List, Optional, Tuple, Type, Dict, Union

from panda3d.core import LRGBColor

from gameplay.yields import Yields
from helpers.colors import Tuple4f
from managers.i18n import T_TranslationOrStr, T_TranslationOrStrOrNone

if TYPE_CHECKING:
    from gameplay.improvement import Improvement


def rgb(r: int, g: int, b: int) -> Tuple[float, float, float] | LRGBColor:
    return (r / 255, g / 255, b / 255)


if TYPE_CHECKING:
    pass


class BaseTerrain(ABC):
    _name: T_TranslationOrStrOrNone = None
    _model: Union[T_TranslationOrStr, Dict[int, str], Callable[..., str], None] = None
    can_spawn_resources: bool = True
    _fallback_color: Tuple[float, float, float] | Tuple4f = rgb(0, 119, 255)

    # This is for things like a forrest, where the terrain is replaced by a new terrain type.
    _warn_user_before_build: bool = False
    _warn_user_before_build_text: T_TranslationOrStr = ""
    _warn_user_before_build_title: T_TranslationOrStr = ""
    uv_index: str = "base"

    def __init__(self):
        self.fallback_color: Tuple[float, float, float] = rgb(225, 0, 255)

        self.name: T_TranslationOrStr = "" if self._name is None else self._name
        self.user_title: T_TranslationOrStr = ""
        self._texture: T_TranslationOrStr = ""

        self.movement_modifier: float = 0.0
        self.water_availability: float = 1.0
        self.radiation_level: float = 0.0

        self.tile_modifiers: Yields = Yields.nullYield()
        self.tile_yield_base: Yields = Yields.nullYield()

        self.passable: bool = True
        self.passable_without_tech: bool = True
        self.model_rotation: Optional[float] = 270

        self._supports_improvements: List[Type["Improvement"]] = []

    @classmethod
    def get_model(cls) -> Union[T_TranslationOrStr, Dict[int, str], Callable[..., str], None]:
        return cls._model

    @classmethod
    def get_fallback_color(cls) -> LRGBColor | Tuple[float, float, float]:
        return cls._fallback_color

    def model(self) -> T_TranslationOrStr:
        # direct string
        if isinstance(self._model, str):
            return self._model

        # factory callable
        if callable(self._model):
            return self._model()

        # percentage-based dict
        if isinstance(self._model, dict):
            # sum only positive percentages
            total_perc = sum(p for p in self._model.keys() if p > 0)
            if total_perc > 100.0:
                raise ValueError(f"Total percentage too high: {total_perc}%")

            rand_val = random.uniform(0.0, 100.0)
            cumulative = 0.0

            for perc, mdl in sorted(self._model.items(), reverse=True):
                if perc <= 0:
                    continue
                cumulative += perc
                if rand_val <= cumulative:
                    return mdl

            # fallback
            if 0.0 in self._model:
                return self._model[0]

            raise ValueError("No model selected (rand_val outside defined % ranges) and no 0% fallback provided.")

        raise ValueError("`_model` must be str, callable, or dict of float→model")

    def texture(self) -> T_TranslationOrStr:
        return self._texture

    def get_tile_yield(self) -> "Yields":
        return self.tile_yield_base

    def add_modifiers(self, modifiers: List["Yields"] | Tuple["Yields", ...]):
        for item in modifiers:
            self.tile_modifiers += item

    def add_modifier(self, modifier: "Yields"):
        self.tile_modifiers += modifier

    def add_tile_yield_modifier(self, yields: "Yields"):
        self.tile_yield_base.add(yields)

    def get_modifiers(self) -> "Yields":
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
