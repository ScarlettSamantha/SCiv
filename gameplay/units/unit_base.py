import random
from abc import ABC
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type

from direct.showbase.Loader import Loader
from direct.showbase.ShowBase import ShowBase
from panda3d.core import BitMask32, LVector3, NodePath

from gameplay.combat.stats import Stats
from managers.i18n import T_TranslationOrStr, t_
from managers.player import PlayerManager
from system.actions import Action
from system.entity import BaseEntity

if TYPE_CHECKING:
    from data.tiles.base_tile import BaseTile
    from gameplay.player import Player
    from gameplay.promotion import PromotionTree


class CantMoveReason(Enum):
    COULD_MOVE = -1
    NO_MOVES = 0
    NO_PATH = 1
    NO_TARGET = 2
    IMMOBILE = 3
    IMPASSABLE = 4
    NO_OWNER = 5
    OTHER_OWNER = 6
    NO_UNIT = 7
    UNIT_TRAPPED_WIDWAY = 8


class UnitBaseClass(BaseEntity, ABC):
    _model: Optional[str] = None

    def __init__(
        self,
        key: str,
        name: T_TranslationOrStr,
        description: T_TranslationOrStr,
        base: ShowBase,
        icon: str | None,
        promotion_tree: Type["PromotionTree"],
        owner: Optional["Player"] = None,
        model: Optional[NodePath] = None,
        model_rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        model_size: float = 1.0,
        model_position_offset: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        *args: Any,
        **kwargs: Any,
    ):
        self.key: str = key
        self.name: T_TranslationOrStr = name
        self.description: T_TranslationOrStr = description
        self.icon: str | None = icon
        self.promotion_tree: Type[PromotionTree] = promotion_tree
        self.owner: Player | None = owner
        self.tile: BaseTile  # Tile must be set before spawning
        self.model: Optional[NodePath] = model  # Will hold the Panda3D model
        self.model_size: float = model_size  # Default size of the model
        self.model_rotation: Tuple[float, float, float] = model_rotation  # Default rotation of the model
        self.model_position_offset: Tuple[float, float, float] = model_position_offset
        self.base: ShowBase = base
        self.collides: bool = True
        self.tag: Optional[str] = None
        self.actions: List[Action] = []

        self.pos_y: float = 0.0
        self.pos_x: float = 0.0
        self.pos_z: float = 0.0

        self.max_health: int = 100
        self.current_health: int = 100

        self.max_attacks: int = 1
        self.attacks_left: int = 1

        self.stats: Stats = Stats()
        # 1 is mele
        self.range: int = 1
        self.in_direct: bool = False

        self.max_moves: int = 10
        self.moves_left: int | float = 10.0

        self.can_swim: bool = False
        self.can_fly: bool = False

        self.can_move: bool = True
        self.can_attack: bool = True
        self.can_heal: bool = True
        self.can_pillage: bool = True
        self._register()

    def _register(self):
        self.add_action(Action(name=t_("actions.unit.self_destroy"), action=self.destroy))

    def register(self) -> None:
        from managers.entity import EntityManager, EntityType

        entity_manager: EntityManager = EntityManager.get_instance()

        entity_manager.register(entity=self, type=EntityType.UNIT, key=self.tag if self.tag else self.key)

        if self.owner is not None:
            self.owner.units.add_unit(entity_manager.get_ref(EntityType.UNIT, str(self.tag), weak_ref=True))

    def set_pos(self, pos: Tuple[float, float, float]) -> None:
        self.pos_x, self.pos_y, self.pos_z = pos
        self.model.setPos(LVector3(*pos))

    def unregister(self) -> None:
        from managers.entity import EntityManager, EntityType

        EntityManager.get_instance().unregister(entity=self, type=EntityType.UNIT)

    def spawn(self) -> bool:
        """
        Spawns the unit at its assigned tile, loading the model into Panda3D.
        Returns True if successful, False otherwise.
        """
        if self.tile is None:
            raise ValueError(f"Unit {self.key} cannot spawn without an assigned tile.")

        if not self.tile.is_occupied():  # Assumed tile method
            raise ValueError(f"Tile at {self.tile.get_cords()} is not passable.")

        if not isinstance(self._model, str):
            raise ValueError(f"Unit {self.key} has no model assigned.")

        # Load the Panda3D model and position it at the tile
        self.model = self.load_model(self._model)

        if not self._model:
            raise RuntimeError(f"Failed to load model for unit {self.key}")

        print(f"Unit {self.key} spawned at {self.tile.get_cords()} with model {self._model}")
        return True

    def get_actions(self) -> List[Action]:
        return self.actions

    def move(self, action: Action, _args: List[Any], kwargs: Dict[str, Any]) -> CantMoveReason:
        if "tile" not in kwargs:
            raise ValueError("No tile provided to move action.")

        from gameplay.repositories.tile import TileRepository

        target_tile: BaseTile = kwargs["tile"]

        if not self.can_move:
            return CantMoveReason.IMMOBILE

        if self.moves_left <= 0:
            return CantMoveReason.NO_MOVES

        if target_tile.passable is False:
            return CantMoveReason.IMPASSABLE

        result_tile: Optional[BaseTile] = self.tile  # Start off at our current tile
        if not target_tile.is_occupied() and self.tile_is_occupiable(target_tile):
            if self.model is not None:
                # Attempt pathfinding
                if (tiles_to_move := TileRepository.astar(self.tile, target_tile, 1.0)) is None:
                    return CantMoveReason.NO_PATH

                for tile in tiles_to_move:
                    # Before stepping onto 'tile', store our current tile as the fallback
                    previous_tile = result_tile

                    # Check if we have enough movement to step onto this tile
                    if (self.moves_left - tile.movement_cost) < 0:
                        # Not enough moves left; revert to the previous tile's position
                        if previous_tile is not None:
                            self.set_pos((tile.get_cords()[0], tile.get_cords()[1], self.pos_z))
                        return CantMoveReason.NO_MOVES

                    # Check if tile is still valid for the unit
                    if tile.is_visisted_by(self) is False:
                        # Move partially onto this tile and then get trapped or do partial logic
                        cords = tile.get_cords()
                        self.set_pos(cords[0], cords[1], self.pos_z)
                        return CantMoveReason.UNIT_TRAPPED_WIDWAY

                    # If we got here, we can step onto tile
                    result_tile = tile
                    self.moves_left -= tile.movement_cost

        if result_tile is not None and self.model is not None:
            result_cords = result_tile.get_cords()
            self.set_pos((result_cords[0], result_cords[1], self.pos_z))

        if result_tile == target_tile:
            return CantMoveReason.COULD_MOVE
        elif result_tile is None:
            return CantMoveReason.NO_PATH
        return CantMoveReason.NO_MOVES

    def add_action(self, action: Action) -> None:
        self.actions.append(action)

    def remove_action(self, action: Action) -> None:
        self.actions.remove(action)

    def load_model(self, model_path: str) -> NodePath | None:
        loader: Loader = Loader(self.base)
        model: Optional[NodePath] = loader.loadModel(model_path)
        if not model:
            return None

        if self.tile is None:
            raise ValueError(f"Unit {self.key} cannot spawn without an assigned tile.")

        # Position and transform the model
        tile_pos = self.tile.get_cords()
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
            model.setCollideMask(BitMask32.bit(1))
        else:
            model.setCollideMask(BitMask32.allOff())

        self.tag = f"unit_{self.key}_{random.randint(0, 10000)}"
        model.setTag("tile_id", self.tag)
        model.reparentTo(self.base.render)  # Attach model to scene graph

        self.register()

        return model

    def tile_is_occupiable(self, tile: "BaseTile") -> bool:
        return tile.is_passable()

    def set_color(self, color: Tuple[float, float, float, float]) -> None:
        if isinstance(self.model, str) and not isinstance(self.model, NodePath):
            raise ValueError(f"Unit {self.key} has no model assigned.")
        if self.model is not None:
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
            "tile": self.tile.tag if self.tile is not None else "None",
            "health": f"{self.current_health}/{self.max_health}",
            "attacks": f"{self.attacks_left}/{self.max_attacks}",
            "damage": self.stats.attack_modifier,
            "defense": self.stats.defense_modifier,
            "armor_piercing": self.stats.armor_piercing,
            "movement": f"{self.moves_left}/{self.max_moves}",
            "range": self.range,
            "can_move": self.can_move,
            "can_attack": self.can_attack,
            "can_heal": self.can_heal,
            "can_pillage": self.can_pillage,
        }

    def destroy(self, *args, **kwargs) -> bool:
        """Removes the unit from the scene and cleans up references."""
        if self.model:
            self.model.removeNode()  # Remove from the scene graph
            self.model = None  # Clear reference

        # Remove from the units lookup dictionary if it exists
        self.unregister()

        # Nullify references to break cyclic dependencies
        self.tile.units.remove_unit(self)

        if self.owner is not None:
            self.owner.units.remove_unit(self)

        self.owner = None
        self.actions.clear()
        self.tag = None
        return True

    @classmethod
    def get_unit_by_tag(cls, tag: str) -> Optional["UnitBaseClass"]:
        from managers.entity import EntityManager, EntityType

        entity: UnitBaseClass | BaseEntity | None = EntityManager.get_instance().get(EntityType.UNIT, tag)
        if isinstance(entity, UnitBaseClass):
            return entity
        return None
