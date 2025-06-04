import random
from abc import ABC
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type, Union, overload

from direct.showbase.Loader import Loader
from direct.showbase.MessengerGlobal import messenger
from panda3d.core import BitMask32, LVector3, NodePath


from gameplay.condition import Condition
from gameplay.repositories.tile import TileRepository
from gameplay.resources.core.basic.production import Production
from main import Cache
from managers.combat import T_TARGET, Combat
from managers.combat_log import CombatLog
from managers.entity import uuid4
from managers.i18n import T_TranslationOrStrOrNone
from managers.player import PlayerManager
from managers.unit import UnitManager
from system.actions import Action
from system.effects import Effects
from system.entity import BaseEntity

if TYPE_CHECKING:
    from gameplay.improvement import BasicBaseResource
    from gameplay.player import Player
    from gameplay.promotion import PromotionTree
    from gameplay.tiles.base_tile import BaseTile


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

    def __init__(self, tile: "BaseTile", key: Optional[str] = None):
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

        self.can_swim: bool = False
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

        self.logger = Cache.get_showbase_instance().logger.get_singleton_instance().gameplay.getChild("unit")

        self.register_actions()

    def register_actions(self): ...

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

    @overload
    def set_pos(self, pos: Tuple[float, float, float], maintain_z: bool = True) -> None: ...

    @overload
    def set_pos(self, pos: "BaseTile", maintain_z: bool = True, set_as_tile: bool = True) -> None: ...

    def set_pos(
        self, pos: Union[Tuple[float, float, float], "BaseTile"], maintain_z: bool = True, set_as_tile: bool = True
    ) -> None:
        if isinstance(pos, tuple):
            if maintain_z:
                self.pos_x, self.pos_y, _ = pos
            else:
                self.pos_x, self.pos_y, self.pos_z = pos
        else:
            if maintain_z:
                (self.pos_x, self.pos_y, _) = pos.get_cords()
            else:
                (self.pos_x, self.pos_y, self.pos_z) = pos.get_cords()
            if set_as_tile:
                self.tile = pos

        if self.model is not None:  # type: ignore
            self.model.setPos(LVector3(self.pos_x, self.pos_y, self.pos_z + self.get_tile().pos_z))  # type: ignore

    def is_alive(self) -> bool:
        return self.health() > 0

    def unregister(self) -> None:
        from managers.entity import EntityManager, EntityType

        EntityManager.get_singleton_instance().unregister(entity=self, type=EntityType.UNIT)
        UnitManager.get_singleton_instance().remove_unit(self)

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
        self.model = self.load_model(self._model)
        self.get_tile().rerender()

        if not self._model:
            raise RuntimeError(f"Failed to load model for unit {self.key}")

        self.logger.debug(f"Unit {self.key} spawned at {self.get_tile().get_cords()} with model {self._model}")
        return True

    def get_model_path(self) -> Optional[str]:
        """
        Returns the model path of the unit.
        """
        if isinstance(self._model, str):
            return self._model
        return None

    @classmethod
    def spawn_on(cls, tile: "BaseTile", player: "Player", ignore_constraints: bool = False) -> "Unit":
        instance = cls(tile=tile)
        instance.owner = player

        player.units.add_unit(instance)
        tile.add_unit(instance)
        UnitManager.get_singleton_instance().add_unit(instance)

        return instance

    def get_actions(self) -> List[Action]:
        return self.actions

    def move(self, tile: "BaseTile") -> CantMoveReason:
        from gameplay.repositories.tile import TileRepository

        target_tile: "BaseTile" = tile

        if not self.can_move:
            return CantMoveReason.IMMOBILE

        if self.moves_left <= 0:
            return CantMoveReason.NO_MOVES

        if target_tile.passable is False:
            return CantMoveReason.IMPASSABLE

        if len(target_tile.units) > 0:
            return CantMoveReason.OTHER_UNIT_ON_TILE

        if self.model is None:  # type: ignore
            raise ValueError(f"Unit {self.key} has no model assigned.")

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

        result_tile: "BaseTile" = self.get_tile()  # Start off at our current tile
        self.get_tile().get_units().remove_unit(self)  # Remove from the current tile
        for _tile in tiles_to_move:
            _tile: "BaseTile" = _tile  # this is a type hint
            cords: Tuple[float, float, float] = _tile.get_cords()

            if (self.moves_left - _tile.movement_cost) < 0:
                previous_tile_cords: Tuple[float, float, float] = (
                    result_tile.get_cords()
                )  # previous due to the fact that we are not on the tile yet and have not updated the result_tile
                self.tile = result_tile
                self.set_pos((previous_tile_cords[0], previous_tile_cords[1], self.pos_z + _tile.pos_z))
                return CantMoveReason.NO_MOVES

            # Check if tile is still valid for the unit
            if _tile.is_visisted_by(self) is False:
                # Move partially onto this tile and then get trapped or do partial logic
                self.moves_left -= _tile.movement_cost
                self.set_pos((cords[0], cords[1], self.pos_z + cords[2]))
                self.tile = _tile
                return CantMoveReason.UNIT_TRAPPED_MIDWAY

            # If we got here, we can step onto tile
            result_tile.remove_unit(self)
            result_tile.rerender()
            result_tile: "BaseTile" = _tile
            self.moves_left -= _tile.movement_cost
            self.tile = _tile
            self.set_pos((cords[0], cords[1], self.pos_z + _tile.pos_z))

            _tile.add_unit(self)  # Add to the new tile
            self.get_tile().rerender()  # Rerender the tile
        if result_tile == target_tile:
            return CantMoveReason.COULD_MOVE
        return CantMoveReason.NO_MOVES

    def add_action(self, action: Action) -> None:
        self.actions.append(action)

    def remove_action(self, action: Action) -> None:
        self.actions.remove(action)

    def load_model(self, model_path: str) -> NodePath | None:
        from gameplay.tiles.base_tile import BaseTile

        loader: Loader = Loader(self.base)
        model: Optional[NodePath] = loader.loadModel(model_path)
        if not model:
            return None

        if isinstance(self.tile, BaseTile):
            self.tile.unit_icons_np = None
        if self.tile is None:
            raise ValueError(f"Unit {self.key} cannot spawn without an assigned tile.")

        # Position and transform the model
        tile_pos = self.get_tile().get_cords()
        pos = (
            tile_pos[0] + self.model_position_offset[0],
            tile_pos[1] + self.model_position_offset[1],
            tile_pos[2] + self.model_position_offset[2],
        )
        model.setPos(LVector3(*pos))
        model.setHpr(LVector3(*self.model_rotation))
        model.setScale(self.model_size)

        self.pos_x, self.pos_y, self.pos_z = pos

        if self.collides:
            model.setCollideMask(BitMask32.bit(1))  # type: ignore
        else:
            model.setCollideMask(BitMask32.allOff())  # type: ignore

        model.setTag("tile_id", self.tag)
        model.reparentTo(self.base.render)

        return model

    def generate_unit_tag(self) -> str:
        if self.owner is not None:
            return f"unit_{self.owner.id}_{self.key}_{random.randint(0, 1000000)}"
        else:
            return f"unit_{self.key}_{random.randint(0, 1000000)}"

    def tile_is_occupiable(self, tile: "BaseTile") -> bool:
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

    def to_gui(self) -> Dict[str, Any]:
        if self.owner is None:
            owner_name = PlayerManager.get_nature()
        else:
            owner_name = self.owner.civilization.name
        return {
            "tag": self.tag,
            "key": self.key,
            "name": str(self.name),
            "description": self.description,
            "owner": owner_name,
            "cords": f"{round(self.pos_x, 5)}, {round(self.pos_y, 5)}, {round(self.pos_z, 5)}",
            "tile": self.get_tile().tag if self.tile is not None else "None",
            "health": f"{self.health()}/{self.max_health}",
            "damage": f"Mele: {self.get_attack_power_mele()} | Ranged: {self.get_attack_power_ranged()}",
            "defense": f"Mele: {self.get_defense_mele()} | Ranged: {self.get_defense_ranged()}",
            "attack_points": f"{self.attack_points_left}/{self.attack_points}",
            "attack_points_cost": f"Mele: {self.attack_points_cost_mele} | Ranged: {self.attack_points_cost_ranged}",
            "attack_range": self.attack_range,
            "movement": f"{self.moves_left}/{self.max_moves}",
            "can_move": self.can_move,
            "can_attack": self.can_attack,
            "can_heal": self.can_heal,
            "can_pillage": self.can_pillage,
            "can_build": self.can_build,
        }

    def destroy(self, as_system: bool = False, *args: Any, **kwargs: Any) -> None:
        """Removes the unit from the scene and cleans up references."""
        if self.model:  # type: ignore
            self.model.removeNode()  # type: ignore # Remove from the scene graph
            self.model = None  # Clear reference

        # Remove from the units lookup dictionary if it exists
        self.unregister()

        # Nullify references to break cyclic dependencies
        self.get_tile().get_units().remove_unit(self)

        if self.owner is not None:
            self.owner.units.remove_unit(self)

        self.owner = None
        self.actions.clear()
        self.get_tile().rerender()
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

    def look(self, radius: int) -> List["BaseTile"]:
        return TileRepository.get_neighbors(self.get_tile(), radius, False, False)

    def attack(self, target: T_TARGET) -> None:
        outcome = Combat.attack(self, target)
        CombatLog.add_entry(entry=CombatLog.entry_from_outcome(outcome=outcome))  # type: ignore
