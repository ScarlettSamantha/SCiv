import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Callable, Dict, Tuple, Union

from gameplay.yields import Yields
from managers.entity import EntityType
from managers.i18n import T_TranslationOrStrOrNone
from system.entity import BaseEntity

if TYPE_CHECKING:
    from gameplay.city import City
    from gameplay.player import Player
    from gameplay.tiles.base_tile import BaseTile
    from gameplay.units.unit_base import UnitBaseClass
    from managers.world import World


class EffectType(Enum):
    TILE = 0
    CITY = 1
    PLAYER = 2
    GLOBAL = 3


parent_types = Union["City", "BaseTile", "Player", "World", "UnitBaseClass"]


class Effects:
    def __init__(self, parent: parent_types) -> None:
        self.parent: parent_types = parent
        self._effects = {}
        self._effects_num: int = 0

    def add_effect(
        self,
        effect: "Effect",
        auto_register: bool = True,
        execute_on_add: bool = True,
        auto_add_parent_on_effect: bool = True,
    ) -> None:
        self._effects[effect.tag] = effect

        if auto_register and effect.is_registered is False:
            self.register_to_entity_manager(effect)

        if execute_on_add:
            effect.on_effect_applied()

        if auto_add_parent_on_effect:
            self._add_parent_to_effect(effect)

        self._effects_num += 1

    def _add_parent_to_effect(self, effect: "Effect") -> None:
        if isinstance(self.parent, BaseTile) and effect.tile is None:
            effect.tile = self.parent
            if effect.tile.city is not None:
                effect.city = effect.tile.city
        elif isinstance(self.parent, City) and effect.city is None:
            effect.city = self.parent
            effect.tile = self.parent.tile
        elif isinstance(self.parent, Player) and effect.player is None:
            effect.player = self.parent
        elif isinstance(self.parent, World) and effect.world is None:
            effect.world = self.parent

    def _remove_parent_from_effect(self, effect: "Effect") -> None:
        if isinstance(self.parent, BaseTile) and effect.tile is not None:
            effect.tile = None
        elif isinstance(self.parent, City) and effect.city is not None:
            effect.city = None
        elif isinstance(self.parent, Player) and effect.player is not None:
            effect.player = None
        elif isinstance(self.parent, World) and effect.world is not None:
            effect.world = None

    def remove_effect(
        self,
        effect: "Effect",
        auto_unregister: bool = True,
        execute_on_remove: bool = True,
        auto_remove_parent_on_effect: bool = True,
    ) -> None:
        if effect.tag in self._effects:
            if execute_on_remove:
                effect.on_remove()

        if auto_unregister and effect.is_registered:
            self.unregister_from_entity_manager(effect)

        if auto_remove_parent_on_effect:
            self._remove_parent_from_effect(effect)

        del self._effects[effect.tag]
        self._effects_num -= 1

    def register_to_entity_manager(self, effect: "Effect") -> None:
        from managers.entity import EntityManager

        EntityManager.get_instance().register(EntityType.EFFECT, effect)

    def unregister_from_entity_manager(self, effect: "Effect") -> None:
        from managers.entity import EntityManager

        EntityManager.get_instance().register(EntityType.EFFECT, effect)

    def get_effect(self, tag: str) -> "Effect":
        return self._effects[tag]

    def get_effects(self) -> Dict[str, "Effect"]:
        return self._effects

    def clear_effects(self, execute_on_clear: bool = True) -> None:
        if execute_on_clear:
            for effect in self._effects.values():
                effect: "Effect" = effect  # Typehint
                effect.on_clear()

        self._effects.clear()

    def on_turn_end(self, turn: int) -> None:
        total_yield_impact = Yields.nullYield()
        total_maintenance_impact = Yields.nullYield()

        for effect in self._effects.values():
            effect: "Effect" = effect  # Typehint
            effect.on_turn_end()

            total_yield_impact += effect.yield_impact
            total_maintenance_impact += effect.maintenance_impact

            if effect.is_timed and effect.is_expired():
                self.remove_effect(effect)

    def __len__(self) -> int:
        return self._effects_num


def _place_on_tile(tile: "BaseTile", effect: "Effect") -> None:
    tile.effects.add_effect(effect)


def _place_on_players_tile(player: "Player", effect: "Effect") -> None:
    for tile in player.tiles.get_tiles().values():
        tile.effects.add_effect(effect)


def _place_on_city_tiles(city: "City", effect: "Effect") -> None:
    for tile in city.owned_tiles:
        tile.effects.add_effect(effect)


def _place_on_city(city: "City", effect: "Effect") -> None:
    city.effects.add_effect(effect)


def _place_on_player(player: "Player", effect: "Effect") -> None:
    player.effects.add_effect(effect)


def _place_on_world(world: "World", effect: "Effect") -> None:
    world.effects.add_effect(effect)


class EffectPlacers(Enum):
    PLACE_ON_TILE = 0
    PLACE_ON_PLAYERS_TILE = 1
    PLACE_ON_CITY_TILES = 2
    PLACE_ON_CITY = 3
    PLACE_ON_PLAYER = 4
    PLACE_ON_WORLD = 5

    def place(self, base_object: "BaseTile | City | Player | World", effect: "Effect") -> None:
        if self == EffectPlacers.PLACE_ON_TILE and isinstance(base_object, BaseTile):
            _place_on_tile(base_object, effect)
        elif self == EffectPlacers.PLACE_ON_PLAYERS_TILE and isinstance(base_object, Player):
            _place_on_players_tile(base_object, effect)
        elif self == EffectPlacers.PLACE_ON_CITY_TILES and isinstance(base_object, City):
            _place_on_city_tiles(base_object, effect)
        elif self == EffectPlacers.PLACE_ON_CITY and isinstance(base_object, City):
            _place_on_city(base_object, effect)
        elif self == EffectPlacers.PLACE_ON_PLAYER and isinstance(base_object, Player):
            _place_on_player(base_object, effect)
        elif self == EffectPlacers.PLACE_ON_WORLD and isinstance(base_object, World):
            _place_on_world(base_object, effect)
        else:
            raise ValueError("Invalid place method.")


class Effect(BaseEntity, ABC):
    name: T_TranslationOrStrOrNone = None
    description: T_TranslationOrStrOrNone = None
    icon: None | str = None
    visible_to_user: bool = True

    # We can allow both an EffectPlacers enum or a direct Callable as a place_method.
    # But we will store them separately or do a union type. Then when we apply, we check the type.
    place_method: EffectPlacers | Callable[[BaseEntity, "Effect"], None] = EffectPlacers.PLACE_ON_TILE

    activate_on_add: bool = True
    effect_types: Tuple[EffectType] = tuple()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.id: str = uuid.uuid4().hex

        self.tile: "BaseTile | None" = None
        self.city: "City | None" = None
        self.player: "Player | None" = None
        self.world: "World | None" = None

        self.yield_impact: Yields = Yields.nullYield()  # Will be read on turn change
        self.maintenance_impact: Yields = (
            Yields.nullYield()
        )  # Will be read on turn change for the impact it will have on empire wide maintenance.

        self.is_timed: bool = False
        self.duration: int = 0
        self.turns_left: int = 0

        self.active: bool = True

        self.tag: str = self.generate_tag()
        self.register()

    def __del__(self) -> None:
        if self.is_registered:
            self.unregister()

    def register(self):
        from managers.entity import EntityManager

        EntityManager.get_instance().register(EntityType.EFFECT, self)
        self.is_registered = True

    def unregister(self):
        from managers.entity import EntityManager

        EntityManager.get_instance().unregister(EntityType.EFFECT, self)
        self.is_registered = False

    def generate_tag(self) -> str:
        if self.tile is None and self.city is not None:  # is a city effect
            return f"{self.__class__.__name__}_city_{self.city.name}_{self.id}"
        elif self.tile is not None and self.city is None:  # is a tile effect
            return f"{self.__class__.__name__}_tile_{self.tile.x}_{self.tile.y}_{self.id}"
        else:  # is a global effect
            return f"{self.__class__.__name__}_{self.id}"

    def apply(self, base_object: "BaseTile | City | Player | World") -> None:
        if isinstance(self.place_method, EffectPlacers):
            self.place_method.place(base_object, self)
        elif isinstance(self.place_method, Callable) and isinstance(base_object, BaseEntity):
            self.place_method(base_object, self)
        else:
            raise ValueError("Invalid place method.")

    def activate(self, execute_on_activate: bool = True) -> None:
        self.active = True

        if execute_on_activate:
            self.on_activate()

    def deactivate(self, execute_on_deactivate: bool = True) -> None:
        self.active = False

        if execute_on_deactivate:
            self.on_deactivate()

    def on_turn_end(self) -> None:
        if self.active is not True:
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

    def is_expired(self) -> bool:
        return self.turns_left <= 0

    @abstractmethod
    def on_city_turn_end(self) -> None: ...  # If the object has a city effect, this will be called on turn end.
    @abstractmethod
    def on_tile_turn_end(self) -> None: ...  # If the object has a tile effect, this will be called on turn end.
    @abstractmethod
    def on_player_turn_end(self) -> None: ...  # If the object has a player effect, this will be called on turn end.
    @abstractmethod
    def on_global_turn_end(self) -> None: ...  # If the object has a global effect, this will be called on turn end.

    @abstractmethod
    def on_activate(self) -> None: ...  # Will be called when the effect is activated.
    @abstractmethod
    def on_deactivate(self) -> None: ...  # Will be called when the effect is deactivated.
    @abstractmethod
    def on_effect_applied(self) -> None: ...  # Will be called when the effect is applied.
    @abstractmethod
    def on_effect_expire(self) -> None: ...  # Will be called when the effect expires.
    @abstractmethod
    def on_clear(self) -> None: ...  # Will be called when a clear has been called on the parent.
    @abstractmethod
    def on_remove(self) -> None: ...  # Will be called when the effect is removed from the parent.
