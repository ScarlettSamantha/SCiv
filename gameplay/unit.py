import random
from abc import ABC
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type

from direct.showbase.Loader import Loader
from direct.showbase.MessengerGlobal import messenger
from panda3d.core import BitMask32, LVector3, NodePath, PandaNode


from direct.showbase import MessengerGlobal
from gameplay.condition import Condition
from gameplay.floating_text import spawn_damage_text
from gameplay.repositories.tile import TileRepository
from gameplay.resources.core.basic.production import Production
from helpers.debug import Debug
from main import Cache
from managers.combat import T_TARGET, Combat, CombatResults
from managers.combat_log import CombatLog
from managers.entity import uuid4
from managers.i18n import T_TranslationOrStrOrNone
from managers.input import NET_NODE_TAG_ID_FIELD, NET_TYPE, NET_TYPE_FIELD
from managers.unit import UnitManager
from system.actions import Action
from system.effects import Effects
from system.entity import BaseEntity

if TYPE_CHECKING:
    from gameplay.improvement import BasicBaseResource
    from gameplay.player import Player
    from gameplay.promotion import PromotionTree
    from gameplay.tile import Tile


class CantMoveReason(Enum):
    SAME_TILE = -2  # This is a special case where the unit is already on the tile
    COULD_MOVE = -1  # This is more of a ok unit could move.
    NO_MOVES = 0  # This is when the unit has no moves left
    NO_PATH = 1  # This is when the unit has no path to the target
    NO_TARGET = 2  # This is when the unit has no target this is a bug.
    IMMOBILE = 3  # This is when the unit is immobile and cannot move.
    IMPASSABLE = 4  # This is only when the target tile is impassable as otherwise routing would have caught it. and trigger NO_PATH
    NO_OWNER = 5  # This is when the unit has no owner
    OTHER_OWNER = 6  # This is when the target tile is owned by another player this can integrate with the other owner in some way.
    NO_UNIT = 7  # This is when the unit has no unit to move this is a bug.
    UNIT_TRAPPED_MIDWAY = 8  # This is when the unit is trapped midway through the path as the tiles have an on_visit check which can be used to trap the unit this can be used to do partial logic.
    OTHER_UNIT_ON_TILE = 9  # This might have to integrate with the other owner in some way ether being it attacking or being attacked or just not being able to move.


class Unit(BaseEntity, ABC):
    _model: Optional[str] = None

    buildable: bool = False
    build_conditions: Dict[str, Condition] = {}
    name: T_TranslationOrStrOrNone
    description: T_TranslationOrStrOrNone
    icon: str | Path | None
    promotion_tree: Type["PromotionTree"]
    model: Optional[NodePath] = None
    model_size: float = 1.0

    can_spawn_on_land: bool = True
    can_spawn_on_water: bool = False
    max_health: float = 10.0

    def __init__(self, tile: "Tile", key: Optional[str] = None):
        from gameplay.city import Yields  # to avoid circular import

        BaseEntity.__init__(self, tile=tile)

        self.key: str = key if key else uuid4().hex

        self.owner: Player | None = None
        self.model_rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # Default rotation of the model
        self.model_position_offset: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.collides: bool = True
        self.tag: str = self.generate_unit_tag()
        self.actions: List[Action] = []

        self.pos_y: float = 0.0
        self.pos_x: float = 0.0
        self.pos_z: float = 0.0

        self.max_moves: int = 10
        self.moves_left: int | float = 10.0

        self.can_cross_water: bool = self.can_spawn_on_water
        self.can_cross_land: bool = self.can_spawn_on_land
        self.can_fly: bool = False

        self.can_move: bool = True
        self.can_attack: bool = True
        self.can_heal: bool = True
        self.can_pillage: bool = True
        self.can_build: bool = False

        self.resource_needed: Type["BasicBaseResource"] = Production
        self.amount_resource_needed: Yields = Yields(production=10)

        self.effects: Effects = Effects(self)

        self.build_charges: int = 0
        self.build_charges_left: int = 0

        self._logger = None

        self.model_cache: Optional[NodePath] = None

        self.register_actions()
        self.register()

    def register_actions(self): ...

    @property
    def logger(self):
        if self._logger is None:
            self._logger = Cache.get_showbase_instance().logger.get_singleton_instance().gameplay.getChild("unit")
        return self._logger

    def get_pos(self) -> Tuple[float, float, float]:
        return (self.pos_x, self.pos_y, self.pos_z)

    def on_load(self):
        self.base = Cache.get_showbase_instance()
        self.spawn(ignore_constraints=True)

    def register(self) -> None:
        from managers.entity import EntityManager, EntityType

        entity_manager: EntityManager = EntityManager.get_singleton_instance()

        entity_manager.register(entity=self, type=EntityType.UNIT, key=self.tag)

        if self.owner is not None:
            self.owner.units.add_unit(entity_manager.get(EntityType.UNIT, str(self.tag)))  # type: ignore

        UnitManager.get_singleton_instance().add_unit(self)

    def set_pos(self, pos: Tuple[float, float, float]) -> None:
        self.pos_x, self.pos_y, self.pos_z = pos

    def is_alive(self) -> bool:
        return self.health() > 0

    def unregister(self) -> None:
        from managers.entity import EntityManager, EntityType

        EntityManager.get_singleton_instance().unregister(entity=self, type=EntityType.UNIT)
        UnitManager.get_singleton_instance().remove_unit(self)

    def render(self) -> NodePath | None:
        if self.model is not None:
            self.unload_model()

        self.model = self.load_model()

        if self.model is None:
            self.logger.error(f"Failed to load model for unit {self.key} at path {self._model}")
            return None

        return self.model

    def spawn(self, ignore_constraints: bool = False) -> bool:
        """
        Spawns the unit at its assigned tile, loading the model into Panda3D.
        Returns True if successful, False otherwise.
        """
        if self.tile is None:
            raise ValueError(f"Unit {self.key} cannot spawn without an assigned tile.")

        if not isinstance(self._model, str):
            raise ValueError(f"Unit {self.key} has no model assigned.")

        if self.is_registered is False:
            self.register()

        # Load the Panda3D model and position it at the tile
        self.render()

        if self.model:
            self.model.setCollideMask(BitMask32.bit(1))

        if not self._model:
            raise RuntimeError(f"Failed to load model for unit {self.key}")

        if Debug.world_spawning():
            self.logger.debug(f"Unit {self.key} spawned at {self.get_tile().get_cords()} with model {self._model}")
        return True

    def get_model_path(self) -> Optional[str]:
        """
        Returns the model path of the unit.
        """
        if isinstance(self._model, str):
            return self._model
        return None

    def get_actions(self) -> List[Action]:
        return self.actions

    @classmethod
    def spawn_on(cls, tile: "Tile", player: "Player", ignore_constraints: bool = False) -> "Unit":
        if (
            not ignore_constraints
            and (cls.can_spawn_on_water and tile.is_land)
            and (cls.can_spawn_on_land and tile.is_water)
        ):
            raise ValueError(f"Unit {cls.__name__} cannot spawn on tile {tile.tag} due to constraints.")

        if tile.is_passable is False:
            raise ValueError(f"Unit {cls.__name__} cannot spawn on impassable tile {tile.tag}.")

        instance = cls(tile=tile)
        instance.owner = player
        instance.spawn()

        player.units.add_unit(instance)
        tile.add_unit(instance)
        UnitManager.get_singleton_instance().add_unit(instance)
        tile.render()
        return instance

    def move(self, tile: "Tile") -> CantMoveReason:
        from gameplay.repositories.tile import TileRepository

        target_tile: "Tile" = tile

        if not self.can_move:
            return CantMoveReason.IMMOBILE

        if self.moves_left <= 0:
            return CantMoveReason.NO_MOVES

        if target_tile.passable is False:
            return CantMoveReason.IMPASSABLE

        if len(target_tile.units) > 0:
            return CantMoveReason.OTHER_UNIT_ON_TILE

        tiles_to_move = []
        # Attempt pathfinding
        if self.tile is not None and (tiles_to_move := TileRepository.astar(self.get_tile(), target_tile, 1.0)) is None:
            return CantMoveReason.NO_PATH

        # This was a bug for a while, but it was fixed
        if (len(tiles_to_move) - 1) == 0:
            return CantMoveReason.SAME_TILE

        if self.tile is None:
            raise AssertionError(f"Unit {self.key} has no tile assigned.")

        if tiles_to_move[0] == self.get_tile():
            del tiles_to_move[0]  # Remove the first tile as it is the current tile

        departing_tile: "Tile" = self.get_tile()  # Start off at our current tile
        current_tile: "Tile" = self.get_tile()

        for _tile in tiles_to_move:
            if (self.moves_left - _tile.movement_cost) < 0:
                self._move_to_tile(current_tile, departing_tile)
                return CantMoveReason.NO_MOVES

            self.moves_left -= _tile.movement_cost

            if _tile.is_visisted_by(self) is False:
                # Move partially onto this tile and then get trapped or do partial logic
                self._move_to_tile(_tile, departing_tile)
                return CantMoveReason.UNIT_TRAPPED_MIDWAY

            current_tile = _tile

        self._move_to_tile(current_tile, departing_tile)  # Move to the last tile in the path
        if current_tile == target_tile:
            return CantMoveReason.COULD_MOVE
        return CantMoveReason.NO_MOVES

    def _clear_departing_tile(self, tile: "Tile") -> None:
        tile.remove_unit(self)
        self.unload_model()
        tile.render()

    def _move_to_tile(self, tile: "Tile", clear_departing_tile: Optional["Tile"] = None) -> None:
        if clear_departing_tile is not None:
            self._clear_departing_tile(clear_departing_tile)

        self.set_tile(tile)
        self.model = self.load_model()
        self.calculate_model_position()
        self.get_tile().add_unit(self)
        self.get_tile().render()

    def calculate_model_position(self) -> None:
        """
        Calculates the position of the model based on the tile's coordinates and the unit's model position offset.
        This is used to ensure the model is positioned correctly on the tile.
        """
        if self.model is None:
            return None

        self.pos_x, self.pos_y, self.pos_z = pos = self.get_tile().calculate_z_pos_on_altitude()
        self.model.setPos(*pos)  # type: ignore
        self.model.setHpr(LVector3(*self.model_rotation))
        self.model.setScale(self.model_size)

    def add_action(self, action: Action) -> None:
        self.actions.append(action)

    def remove_action(self, action: Action) -> None:
        self.actions.remove(action)

    def unload_model(self) -> None:
        """
        Unloads the model from the scene and clears the reference.
        This is used when the unit is destroyed or removed from the scene.
        """
        if self.model is not None:
            self.model.removeNode()
            self.model = None
        else:
            self.logger.warning(f"Unit {self.key} has no model to unload.")

    def load_model(self) -> NodePath | None:
        loader: Loader = Loader(self.base)
        model_path: Optional[str] = self.get_model_path()

        if model_path is None:
            raise ValueError(f"Unit {self.key} has no model path defined.")

        if not self.model_cache:
            model: NodePath[PandaNode] | None = loader.loadModel(model_path)  # type: ignore
            if model is None:  # type: ignore
                raise RuntimeError(f"Failed to load model for unit {self.key} at path {model_path}")
            self.model_cache = model

        model: NodePath = self.model_cache.copyTo(self.base.render)

        if self.tile is None:
            raise ValueError(f"Unit {self.key} cannot spawn without an assigned tile.")

        tile_pos = self.get_tile().get_cords()
        pos = (
            tile_pos[0],
            tile_pos[1],
            self.get_tile().calculate_z_pos_on_altitude()[2],
        )
        model.setPos(*pos)
        model.setHpr(LVector3(*self.model_rotation))
        model.setScale(self.model_size)

        self.pos_x, self.pos_y, self.pos_z = pos

        if self.collides:
            model.setCollideMask(BitMask32.bit(1))  # type: ignore
        else:
            model.setCollideMask(BitMask32.allOff())  # type: ignore

        model.setTag(NET_TYPE_FIELD, NET_TYPE.MODEL.value)
        model.setTag(NET_NODE_TAG_ID_FIELD, self.tag)

        return model

    def generate_unit_tag(self) -> str:
        if self.owner is not None:
            return f"unit_{self.owner.id}_{self.key}_{random.randint(0, 1000000)}"
        else:
            return f"unit_{self.key}_{random.randint(0, 1000000)}"

    def tile_is_occupiable(self, tile: "Tile") -> bool:
        return tile.is_passable() and len(tile.units) == 0

    def restore_movement_points(self) -> None:
        """Resets the unit's movement points to the maximum value. Called by the Turn manager."""
        self.moves_left = self.max_moves

    def drain_movement_points(self, cost_or_zero: float | None = None) -> None:
        if cost_or_zero is None:
            self.moves_left = 0
        else:
            self.moves_left -= cost_or_zero

    def set_color(self, color: Tuple[float, float, float, float]) -> None:
        if isinstance(self.model, str) and not isinstance(self.model, NodePath):  # type: ignore
            raise ValueError(f"Unit {self.key} has no model assigned.")
        if self.model is not None:  # type: ignore
            self.model.setColor(*color)  # type: ignore If check above passes, model is NodePath

    def destroy(self, as_system: bool = False, *args: Any, **kwargs: Any) -> None:
        self.health_left = 0
        self.unregister()

        self.get_tile().remove_unit(self)

        if self.owner is not None:
            self.owner.units.remove_unit(self)

        self.owner = None

        if self.model:  # type: ignore
            self.unload_model()

        self.actions.clear()
        del self.tag

        if as_system:
            messenger.send("system.unit.destroyed", [self])
        else:
            messenger.send("game.gameplay.unit.destroyed", [self])

    @classmethod
    def get_unit_by_tag(cls, tag: str) -> Optional["Unit"]:
        from managers.entity import EntityManager, EntityType

        entity: Unit | BaseEntity | None = EntityManager.get_singleton_instance().get(EntityType.UNIT, tag)
        if isinstance(entity, Unit):
            return entity
        return None

    def look(self, radius: int) -> List["Tile"]:
        return TileRepository.get_neighbors(self.get_tile(), radius, False, False)

    def attack(self, target: T_TARGET) -> None:
        outcome = Combat.attack(self, target)
        entry = CombatLog.entry_from_outcome(outcome=outcome, text=CombatLog.outcome_to_text(outcome=outcome))  # type: ignore

        MessengerGlobal.messenger.send("ui.update.ui.combat_log.add", [entry])

        if isinstance(target, Unit):
            defender_np = target.model
            if defender_np is not None:
                spawn_damage_text(defender_np, outcome.attacker_damage)

        if outcome.status == CombatResults.ATTACKER_KILLED:
            self.kill()
        elif outcome.status == CombatResults.DEFENDER_KILLED:
            target.kill()
