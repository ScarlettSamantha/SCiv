import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Tuple, cast

from direct.showbase.DirectObject import DirectObject
from gameplay.yields import Yields
from helpers.colors import Colors
from helpers.placeholder import Placeholder
from managers.i18n import T_TranslationOrStrOrNone
from system.entity import BaseEntity

if TYPE_CHECKING:
    from gameplay.city import City
    from gameplay.improvement import Improvement
    from gameplay.player import Player
    from gameplay.tile import Tile
    from gameplay.unit import Unit
    from managers.world import World
    from system.effects import EffectPlacers, EffectType


class Effect(BaseEntity, ABC, DirectObject):
    name: T_TranslationOrStrOrNone = None
    description: T_TranslationOrStrOrNone = None
    icon: None | Path | str = Placeholder.getPlaceholderImagePathSmallIcon()
    icon_border_color = Colors.RED
    visible_to_user: bool = True

    _place_method: "EffectPlacers" | Callable[[BaseEntity, "Effect"], None] | None = None

    activate_on_add: bool = True
    effect_types: Tuple["EffectType"] = tuple()  # type: ignore

    def __init__(self, player: "Player", tile: Optional["Tile"] = None, *args: Any, **kwargs: Any) -> None:
        from managers.entity import EntityType
        from system.effects import EffectPlacers

        BaseEntity.__init__(self, tile=tile, owner=player, *args, **kwargs)
        DirectObject.__init__(self)

        self.tag = self.generate_tag()
        self.entity_key = self.tag
        self.entity_type_ref = EntityType.EFFECT.value
        self.owner: "Player" = player
        self.city: "City | None" = None
        self.player: "Player | None" = None
        self.world: bool = False
        self.improvement: "Improvement | None" = None
        self.unit: "Unit | None" = None

        self.place_method: EffectPlacers | Callable[[BaseEntity, Effect], None] = (
            self._place_method if self._place_method is not None else EffectPlacers.PLACE_ON_TILE
        )

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

    def dump(self) -> Dict[str, Any]:
        data = {
            "name": self.name,
            "description": self.description,
            "icon": str(self.icon),
            "icon_border_color": self.icon_border_color,
            "visible_to_user": self.visible_to_user,
            "place_method": self.place_method.__name__ if callable(self.place_method) else str(self.place_method),
            "activate_on_add": self.activate_on_add,
            "effect_types": [et.name for et in self.effect_types],
            "yield_impact": self.yield_impact.dump(),
            "maintenance_impact": self.maintenance_impact.dump(),
            "is_timed": self.is_timed,
            "duration": self.duration,
            "turns_left": self.turns_left,
            "needs_turn_processing": self.needs_turn_processing,
            "active": self.active,
            "entity_key": self.entity_key,
            "entity_type_ref": self.entity_type_ref,
            "tag": self.tag,
            "_health_left": self.health_left,
            "owner_tag": self.owner.get_tag() if self.owner else None,
        }

        owner = self.get_owner().get_tag() if self.get_owner() else None
        if owner:
            data["owner"] = owner

        if self.tile:
            data["tile"] = self.get_tile().get_tag()
        if self.city:
            data["city"] = self.city.get_tag()
        if self.world:
            data["world"] = self.world
        if self.improvement:
            data["improvement"] = self.improvement.get_tag()
        if self.unit:
            data["unit"] = self.unit.get_tag()

        return data

    def load_state(self) -> None:
        from managers.entity import EntityManager, EntityType
        from system.effects import EffectPlacers

        entity_manager: EntityManager = EntityManager.get_singleton_instance()

        place_method_name: str | None = self.place_method if isinstance(self.place_method, str) else None
        if place_method_name:
            if hasattr(EffectPlacers, place_method_name.split(".")[-1]):
                self.place_method = getattr(EffectPlacers, place_method_name.split(".")[-1])
            else:
                raise ValueError(f"Invalid place method: {place_method_name}")

        self.yield_impact = Yields.from_dict(self.yield_impact)  # type: ignore
        self.maintenance_impact = Yields.from_dict(self.maintenance_impact)  # type:ignore

        self.owner = cast("Player", entity_manager.get(EntityType.PLAYER, self.owner_tag))  # type:ignore
        if hasattr(self, "tile") and self.tile:
            self.tile = cast("Tile", entity_manager.get(EntityType.TILE, self.tile))  # type:ignore
        else:
            self.tile = None
        if hasattr(self, "world") and self.world:
            self.city = cast("City", entity_manager.get(EntityType.CITY, self.city))  # type:ignore
        else:
            self.city = None
        if hasattr(self, "improvement") and self.improvement:
            self.improvement = cast("Improvement", entity_manager.get(EntityType.IMPROVEMENT, self.improvement))  # type:ignore
        else:
            self.improvement = None
        if hasattr(self, "unit") and self.unit:
            self.unit = cast("Unit", entity_manager.get(EntityType.UNIT, self.unit))  # type:ignore
        else:
            self.unit = None
        if not hasattr(self, "world") or not self.world:
            self.world = False

        self._health_left = getattr(self, "_health_left", getattr(self, "max_health", 100))

    def register(self):
        from managers.entity import EntityManager, EntityType

        if self.is_registered:
            return

        EntityManager.get_singleton_instance().register(EntityType.EFFECT, self, self.get_tag())
        self.is_registered = True
        self.register_events_handlers()

    @classmethod
    def on_tooltip(cls) -> str:
        return str(cls.name) + "\n\n" + str(cls.description)

    @abstractmethod
    def register_events_handlers(self) -> None: ...

    def unregister(self):
        from managers.entity import EntityManager, EntityType

        EntityManager.get_singleton_instance().unregister(EntityType.EFFECT, self)
        self.is_registered = False

    def generate_tag(self) -> str:
        return f"effect_{uuid.uuid4().hex}"

    def apply(self, base_object: "Tile | City | Player | World | Improvement") -> None:
        if isinstance(self.place_method, EffectPlacers):
            self.place_method.place(base_object, self)
        elif callable(self.place_method) and isinstance(base_object, BaseEntity):
            self.place_method(base_object, self)
        else:
            raise ValueError("Invalid place method.")
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
        from system.effects import EffectType

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
