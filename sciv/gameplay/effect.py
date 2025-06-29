from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, Optional, Tuple, Any
import uuid

from direct.showbase.DirectObject import DirectObject
from gameplay.yields import Yields
from helpers.colors import Colors
from helpers.placeholder import Placeholder
from managers.entity import EntityType
from managers.i18n import T_TranslationOrStrOrNone
from system.effects import EffectPlacers, EffectType
from system.entity import BaseEntity

if TYPE_CHECKING:
    from gameplay.city import City
    from gameplay.improvement import Improvement
    from gameplay.player import Player
    from gameplay.tile import Tile
    from gameplay.unit import Unit
    from managers.world import World


class Effect(BaseEntity, ABC, DirectObject):
    name: T_TranslationOrStrOrNone = None
    description: T_TranslationOrStrOrNone = None
    icon: None | Path | str = Placeholder.getPlaceholderImagePathSmallIcon()
    icon_border_color = Colors.RED
    visible_to_user: bool = True

    # We can allow both an EffectPlacers enum or a direct Callable as a place_method.
    # But we will store them separately or do a union type. Then when we apply, we check the type.
    place_method: EffectPlacers | Callable[[BaseEntity, "Effect"], None] = EffectPlacers.PLACE_ON_TILE

    activate_on_add: bool = True
    effect_types: Tuple[EffectType] = tuple()  # type: ignore

    def __init__(self, player: "Player", tile: Optional["Tile"] = None, *args: Any, **kwargs: Any) -> None:
        BaseEntity.__init__(self, tile=tile, owner=player, *args, **kwargs)
        DirectObject.__init__(self)

        self.id: str = uuid.uuid4().hex
        self.owner: "Player" = player
        self.city: "City | None" = None
        self.player: "Player | None" = None
        self.world: "World | None" = None
        self.improvement: "Improvement | None" = None
        self.unit: "Unit | None" = None

        self.yield_impact: Yields = Yields.nullYield()  # Will be read on turn change
        self.maintenance_impact: Yields = (
            Yields.nullYield()
        )  # Will be read on turn change for the impact it will have on empire wide maintenance.

        self.is_timed: bool = False
        self.duration: int = 0
        self.turns_left: int = 0

        self.needs_turn_processing: bool = False

        self.active: bool = True

    def __del__(self) -> None:
        if self.is_registered:
            self.unregister()

    def __getstate__(self) -> Dict[str, Any]:
        state = self.__dict__.copy()
        if "base" in state:
            del state["base"]
        if "_logger" in state:
            del state["_logger"]

        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        self.__dict__.update(state)
        from managers.log import LogManager
        from sciv.helpers.cache import Cache

        self._logger = LogManager.get_singleton_instance().gameplay.getChild("effect")
        self.base = Cache.get_showbase_instance()

    def register(self):
        from managers.entity import EntityManager

        if self.is_registered:
            return

        self.id = uuid.uuid4().hex

        EntityManager.get_singleton_instance().register(EntityType.EFFECT, self, self.id)
        self.is_registered = True
        self.register_events_handlers()

    @classmethod
    def on_tooltip(cls) -> str:
        return str(cls.name) + "\n\n" + str(cls.description)

    @abstractmethod
    def register_events_handlers(self) -> None: ...

    def unregister(self):
        from managers.entity import EntityManager

        EntityManager.get_singleton_instance().unregister(EntityType.EFFECT, self)
        self.is_registered = False

    def generate_tag(self) -> str:
        return f"{self.__class__.__name__}_{self.id}"

    def apply(self, base_object: "Tile | City | Player | World | Improvement") -> None:
        if isinstance(self.place_method, EffectPlacers):
            self.place_method.place(base_object, self)
        elif callable(self.place_method) and isinstance(base_object, BaseEntity):
            self.place_method(base_object, self)
        else:
            raise ValueError("Invalid place method.")
        if self.tag is None:  # type: ignore
            self.tag = self.generate_tag()
        self.on_place()

    @classmethod
    def apply_to_entity(
        cls,
        base_object: "Tile | City | Player | World | Improvement",
        player: "Player",
        effect: Optional["Effect"] = None,
        auto_register: bool = True,
        execute_on_apply: bool = True,
    ) -> "Effect":
        if effect is None:
            effect = cls(base_object=base_object, player=player)

        if auto_register and not effect.is_registered:
            effect.register()

        effect.apply(base_object)

        if execute_on_apply:
            effect.on_effect_applied()

        return effect

    def activate(self, execute_on_activate: bool = True) -> None:
        self.active = True

        if execute_on_activate:
            self.on_activate()

    def deactivate(self, execute_on_deactivate: bool = True) -> None:
        self.active = False

        if execute_on_deactivate:
            self.on_deactivate()

    def on_turn_end(self) -> None:
        if self.needs_turn_processing is False or self.active is not True or self.is_expired():
            return  # If the effect is not active, we don't want to do anything.

        if self.is_timed:
            self.turns_left -= 1

        if self.turns_left <= 0:
            self.on_effect_expire()

        if EffectType.CITY in self.effect_types:
            self.on_city_turn_end()
        if EffectType.TILE in self.effect_types:
            self.on_tile_turn_end()
        if EffectType.PLAYER in self.effect_types:
            self.on_player_turn_end()
        if EffectType.GLOBAL in self.effect_types:
            self.on_global_turn_end()
        if EffectType.IMPROVEMENT in self.effect_types:
            self.on_improvement_turn_end()
        if EffectType.UNIT in self.effect_types:
            self.on_unit_turn_end()

    def is_expired(self) -> bool:
        return self.turns_left <= 0

    def on_city_turn_end(self) -> None: ...  # If the object has a city effect, this will be called on turn end.
    def on_tile_turn_end(self) -> None: ...  # If the object has a tile effect, this will be called on turn end.
    def on_player_turn_end(self) -> None: ...  # If the object has a player effect, this will be called on turn end.
    def on_global_turn_end(self) -> None: ...  # If the object has a global effect, this will be called on turn end.
    def on_improvement_turn_end(self) -> None: ...
    def on_unit_turn_end(self) -> None: ...

    def on_place(self) -> None: ...
    def on_activate(self) -> None: ...  # Will be called when the effect is activated.
    def on_deactivate(self) -> None: ...  # Will be called when the effect is deactivated.
    def on_effect_applied(self) -> None: ...  # Will be called when the effect is applied.
    def on_effect_expire(self) -> None: ...  # Will be called when the effect expires.
    def on_clear(self) -> None: ...  # Will be called when a clear has been called on the parent.
    def on_remove(self) -> None: ...  # Will be called when the effect is removed from the parent.
