import weakref
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Type, Union, cast

from gameplay.effect import BaseEntityType
from gameplay.yields import Yields

if TYPE_CHECKING:
    from gameplay.city import City
    from gameplay.effect import Effect
    from gameplay.improvement import Improvement
    from gameplay.leader import Leader
    from gameplay.player import Player
    from gameplay.tile import Tile
    from gameplay.unit import Unit
    from managers.world import World


class EffectType(Enum):
    TILE = 0
    CITY = 1
    PLAYER = 2
    GLOBAL = 3
    UNIT = 4
    IMPROVEMENT = 5


parent_types = Union["City", "Tile", "Player", "World", "Unit", "Improvement", "Leader"]


class Effects:
    def __init__(self, parent: parent_types, effects: List[Type["Effect"]] = []) -> None:
        self._parent: weakref.ReferenceType[parent_types] = weakref.ref(parent)
        self._effects: Dict[str, "Effect"] = {}
        self._effects_num: int = 0

    @property
    def parent(self) -> parent_types:
        parent = self._parent()
        if parent is None:
            raise ValueError("Parent has been deleted.")
        return parent

    @parent.setter
    def parent(self, value: parent_types) -> None:
        self._parent = weakref.ref(value)

    def add_effect(
        self,
        effect: "Effect",
        auto_register: bool = True,
        execute_on_add: bool = True,
        auto_add_parent_on_effect: bool = True,
    ) -> None:
        if effect.tag in self._effects:
            raise ValueError(f"Effect with tag {effect.tag} already exists in this Effects instance.")
        self._effects[effect.tag] = effect

        if auto_register and effect.is_registered is False:
            self.register_to_entity_manager(effect)

        if execute_on_add:
            effect.on_effect_applied()

        if auto_add_parent_on_effect:
            self._add_parent_to_effect(effect)

        self._effects_num += 1

    def _add_parent_to_effect(self, effect: "Effect") -> None:
        from gameplay.city import City
        from gameplay.improvement import Improvement
        from gameplay.player import Player
        from gameplay.tile import Tile
        from gameplay.unit import Unit
        from managers.world import World

        if isinstance(self.parent, Tile) and effect.tile is None:
            effect.tile = self.parent
            if effect.tile.city is not None:
                effect.city = effect.tile.city
        elif isinstance(self.parent, City) and effect.city is None:
            effect.city = self.parent
            effect.tile = self.parent.get_tile()
        elif isinstance(self.parent, Player) and effect.player is None:
            effect.player = self.parent
        elif isinstance(self.parent, World) and effect.world is None:  # type:ignore
            effect.world = self.parent
        elif isinstance(self.parent, Unit) and effect.unit is None:
            effect.unit = self.parent
        elif isinstance(self.parent, Improvement) and effect.improvement is None:
            effect.improvement = self.parent

    def _remove_parent_from_effect(self, effect: "Effect") -> None:
        if isinstance(self.parent, "Tile") and effect.tile is not None:
            effect.tile = None
        elif isinstance(self.parent, "City") and effect.city is not None:
            effect.city = None
        elif isinstance(self.parent, "Player") and effect.player is not None:
            effect.player = None
        elif isinstance(self.parent, "World") and effect.world is not None:  # type:ignore
            effect.world = False
        elif isinstance(self.parent, "Unit") and effect.unit is not None:
            effect.unit = None
        elif isinstance(self.parent, "Improvement") and effect.improvement is not None:
            effect.improvement = None

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
        effect.register()

    def unregister_from_entity_manager(self, effect: "Effect") -> None:
        from managers.entity import EntityManager, EntityType

        EntityManager.get_singleton_instance().unregister(EntityType.EFFECT, effect)

    def get_effect(self, tag: str) -> "Effect":
        return self._effects[tag]

    def has(self, effect: Union["Effect", Type["Effect"]]) -> bool:
        if isinstance(effect, str):
            return effect in self._effects
        elif isinstance(effect, type):
            return any(isinstance(e, effect) for e in self._effects.values())
        else:
            return effect.tag in self._effects

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

    def dump(self) -> List[str]:
        return [tag for tag in self._effects.keys()]

    def load_state(self, state: List[str]) -> None:
        from managers.entity import EntityManager, EntityType

        self._effects = {}
        self._effects_num = 0
        for effect_tag in state:
            _effect: weakref.ReferenceType["Effect"] = cast(
                weakref.ReferenceType["Effect"],
                EntityManager.get_singleton_instance().get_ref_weak(EntityType.EFFECT, effect_tag),
            )
            effect: "Effect | None" = _effect()
            if effect is None:
                raise ValueError(f"Effect with tag {effect_tag} not found in EntityManager.")

            self._effects[effect_tag] = effect
            self._effects_num += 1


def _place_on_tile(tile: "Tile", effect: "Effect") -> None:
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


def _place_on_improvement(improvement: "Improvement", effect: "Effect") -> None:
    improvement.effects.add_effect(effect)
    improvement.get_tile().render()


def _place_on_unit(unit: "Unit", effect: "Effect") -> None:
    unit.effects.add_effect(effect)


class EffectPlacers(Enum):
    PLACE_ON_TILE = 0
    PLACE_ON_PLAYERS_TILE = 1
    PLACE_ON_CITY_TILES = 2
    PLACE_ON_CITY = 3
    PLACE_ON_PLAYER = 4
    PLACE_ON_WORLD = 5
    PLACE_ON_UNIT = 6
    PLACE_ON_IMPROVEMENT = 7

    def place(self, base_object: "BaseEntityType", effect: "Effect") -> None:
        from gameplay.city import City
        from gameplay.improvement import Improvement
        from gameplay.player import Player
        from gameplay.tile import Tile
        from managers.world import World

        if self == EffectPlacers.PLACE_ON_TILE and isinstance(base_object, Tile):
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
        elif self == EffectPlacers.PLACE_ON_IMPROVEMENT and isinstance(base_object, Improvement):
            _place_on_improvement(base_object, effect)
        elif self == EffectPlacers.PLACE_ON_UNIT and isinstance(base_object, "Unit"):
            _place_on_unit(base_object, effect)
        else:
            raise ValueError("Invalid place method.")

    def remove(
        self,
        base_object: "Tile | City | Player | World | Improvement",
        effect: "Effect",
        execute_on_remove: bool = True,
    ) -> None:
        from gameplay.city import City
        from gameplay.improvement import Improvement
        from gameplay.player import Player
        from gameplay.tile import Tile
        from managers.world import World

        if self == EffectPlacers.PLACE_ON_TILE and isinstance(base_object, Tile):
            Effect.remove_effect_from_entity(base_object, effect, execute_on_remove=execute_on_remove)
        elif self == EffectPlacers.PLACE_ON_PLAYERS_TILE and isinstance(base_object, Player):
            for tile in base_object.tiles.get_tiles().values():
                Effect.remove_effect_from_entity(tile, effect, execute_on_remove=execute_on_remove)
        elif self == EffectPlacers.PLACE_ON_CITY_TILES and isinstance(base_object, City):
            for tile in base_object.owned_tiles:
                Effect.remove_effect_from_entity(tile, effect, execute_on_remove=execute_on_remove)
        elif self == EffectPlacers.PLACE_ON_CITY and isinstance(base_object, City):
            Effect.remove_effect_from_entity(base_object, effect, execute_on_remove=execute_on_remove)
        elif self == EffectPlacers.PLACE_ON_PLAYER and isinstance(base_object, Player):
            Effect.remove_effect_from_entity(base_object, effect, execute_on_remove=execute_on_remove)
        elif self == EffectPlacers.PLACE_ON_WORLD and isinstance(base_object, World):
            Effect.remove_effect_from_entity(base_object, effect, execute_on_remove=execute_on_remove)
        elif self == EffectPlacers.PLACE_ON_IMPROVEMENT and isinstance(base_object, Improvement):
            Effect.remove_effect_from_entity(base_object, effect, execute_on_remove=execute_on_remove)
            base_object.get_tile().render()
        elif self == EffectPlacers.PLACE_ON_UNIT and isinstance(base_object, "Unit"):
            Effect.remove_effect_from_entity(base_object, effect, execute_on_remove=execute_on_remove)
        else:
            raise ValueError("Invalid place method.")
