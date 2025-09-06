import random
from abc import ABC
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, Type, Union, cast

from gameplay.yields import Yields
from helpers.colors import Tuple4f
from managers.entity import EntityManager
from managers.i18n import T_TranslationOrStr, T_TranslationOrStrOrNone

if TYPE_CHECKING:
    from gameplay.bits import Bit
    from gameplay.improvement import Improvement


def rgb(r: int, g: int, b: int) -> Tuple[float, float, float] | Tuple4f:
    return (r / 255, g / 255, b / 255)


if TYPE_CHECKING:
    pass


class BaseTerrain(ABC):
    _key: str = ""
    _name: T_TranslationOrStrOrNone = None
    _model: Union[T_TranslationOrStr, Dict[int, str], Callable[..., str], None] = (
        "assets/models/terrain/flat_grassland.glb"
    )
    model_scale = (1.72, 1.72, 1.72)
    model_pos_z_offset = -0.05
    model_hpr: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    can_spawn_resources: bool = True
    _fallback_color: Tuple[float, float, float] = (0, 119, 255)

    _warn_user_before_build: bool = False
    _warn_user_before_build_text: T_TranslationOrStr = ""
    _warn_user_before_build_title: T_TranslationOrStr = ""
    uv_map: Tuple[int, int] = (0, 0)

    def __init__(self):
        from gameplay.bits import Bit, Bits

        self.fallback_color: Tuple[float, float, float] = (
            self._fallback_color if self._fallback_color else (0, 119, 255)
        )

        self.name: T_TranslationOrStr = "" if self._name is None else self._name
        self.user_title: T_TranslationOrStr = ""
        self._texture: T_TranslationOrStr = ""

        self.movement_modifier: float = 1.0  # 1.0 is normal, 0.5 is half speed, etc.
        self.water_availability: float = 1.0
        self.radiation_level: float = 0.0

        self.tile_modifiers: Yields = Yields.nullYield()
        self.tile_yield_base: Yields = Yields.nullYield()

        self.passable: bool = True
        self.passable_without_tech: bool = True
        self.model_rotation: Optional[float] = 270

        self.bits: Bits = Bits()
        self.active_bits: List[Bit] = []

        self._supports_improvements: List[Type["Improvement"]] = []

        self.register()

    def dump(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "name": str(self.name),
            "model": str(self._model) if self._model else "",
            "water_availability": self.water_availability,
            "radiation_level": self.radiation_level,
            "tile_yield_base": self.tile_yield_base.dump(),
            "tile_modifiers": self.tile_modifiers.dump(),
            "passable": self.passable,
            "passable_without_tech": self.passable_without_tech,
            "model_rotation": str(self.model_rotation),
            "cls_ref": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "fallback_color": self.fallback_color,
        }
        return data

    def load_state(self, state: Dict[str, Any]) -> None:
        self.name = state.get("name", "")
        self._model = state.get("model", "")
        self.water_availability = state.get("water_availability", 1.0)
        self.radiation_level = state.get("radiation_level", 0.0)
        self.tile_yield_base = Yields.from_dict(state.get("tile_yield_base", {}))
        self.tile_modifiers = Yields.from_dict(state.get("tile_modifiers", {}))
        self.passable = state.get("passable", True)
        self.passable_without_tech = state.get("passable_without_tech", True)
        self.model_rotation = state.get("model_rotation", 270.0)

        fallback_color: Tuple[float, float, float] = cast(
            Tuple[float, float, float], tuple(state.get("fallback_color", (0, 119, 255)))
        )

        if fallback_color:
            self.fallback_color = fallback_color

        uv_map: Tuple[int, int] = cast(Tuple[int, int], tuple(state.get("uv_map", (0, 0))))
        if uv_map:
            self.uv_map = uv_map

        supported_improvements: List[str] = state.get("supported_improvements", [])

        for imp in supported_improvements:
            improvement_class: Type["Improvement"] = EntityManager.get_singleton_instance().dynamic_import(imp)
            if improvement_class not in self._supports_improvements:
                self._supports_improvements.append(improvement_class)

        self._warn_user_before_build = state.get("_warn_user_before_build", False)
        self._warn_user_before_build_text = state.get("_warn_user_before_build_text", "")
        self._warn_user_before_build_title = state.get("_warn_user_before_build_title", "")

    def register(self) -> None:
        self.register_bits()

    @classmethod
    def get_model(cls) -> Union[T_TranslationOrStr, Dict[int, str], Callable[..., str], None]:
        return cls._model

    @classmethod
    def get_fallback_color(cls) -> Tuple[float, float, float] | Tuple4f:
        return cls._fallback_color

    def register_bits(self) -> None:
        pass

    def choose_bits(self, group: Optional[str] = None, num: int = 1) -> List["Bit"]:
        self.active_bits = self.bits.choose()
        return self.active_bits

    def get_bits(self, choose_if_empty: bool = True) -> List["Bit"]:
        if not self.bits:
            if choose_if_empty:
                return self.choose_bits()
            return []
        if not self.active_bits:
            return self.choose_bits()
        return self.active_bits

    def model(self) -> T_TranslationOrStr:
        if isinstance(self._model, str):
            return self._model

        if callable(self._model):
            return self._model()

        if isinstance(self._model, dict):
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

            if 0.0 in self._model:
                return self._model[0]

            raise ValueError("No model selected (rand_val outside defined % ranges) and no 0% fallback provided.")

        raise ValueError("_model must be str, callable, or dict of float model")

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

    def color(self) -> Tuple[float, float, float]:
        return self.fallback_color

    def wall_color(self) -> Tuple[float, float, float]:
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

    def on_spawn(self): ...  # meant for runtime decisions like neighbor evaluation when determining yield.

    def on_build_upon(
        self, improvement: "Improvement"
    ): ...  # this is mostly for things like forests, where the terrain is replaced by a new terrain type.

    def get_atlas_uv(self) -> Tuple[int, int]:
        return self.uv_map

    def on_inspect(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "name": str(self.name),
            "model": str(self._model) if self._model else "",
            "texture": str(self.texture()),
            "fallback_color": str(self.fallback_color),
            "movement_modifier": self.movement_modifier,
            "water_availability": self.water_availability,
            "radiation_level": self.radiation_level,
            "tile_yield_base": self.tile_yield_base.on_inspect(),
            "tile_modifiers": self.tile_modifiers.on_inspect(),
            "passable": self.passable,
            "passable_without_tech": self.passable_without_tech,
            "model_rotation": str(self.model_rotation),
        }
        return data

    @classmethod
    def get_name(cls) -> T_TranslationOrStr:
        return cls._name if cls._name else ""

    @classmethod
    def get_key(cls) -> str:
        return cls._key if cls._key else cls.__name__.lower().replace("_", "-")
