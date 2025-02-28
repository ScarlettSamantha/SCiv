import random
from direct.showbase.ShowBase import ShowBase
from panda3d.core import NodePath, LVector3, BitMask32
from direct.showbase.Loader import Loader
from abc import ABC
from managers.i18n import T_TranslationOrStr, get_i18n, t_
from typing import Callable, Dict, List, Optional, Tuple, Type, Any, TYPE_CHECKING
from gameplay.combat.stats import Stats
from managers.player import PlayerManager
from system.actions import Action
from system.entity import BaseEntity

if TYPE_CHECKING:
    from data.tiles.base_tile import BaseTile
    from gameplay.promotion import PromotionTree
    from gameplay.player import Player


class UnitBaseClass(BaseEntity, ABC):
    units_lookup: Dict[str, "UnitBaseClass"] = {}
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

        self.max_moves: int = 5
        self.moves_left: int = 5

        self.can_swim: bool = False
        self.can_fly: bool = False

        self.can_move: bool = True
        self.can_attack: bool = True
        self.can_heal: bool = True
        self.can_pillage: bool = True
        self._register()

    def _register(self):
        self.add_action(Action(name=t_("actions.unit.self_destroy"), action=self.destroy))

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

    def move(self, _: Action, _args: List[Any], kwargs: Dict[str, Any]) -> Optional[bool]:
        if "tile" not in kwargs:
            raise ValueError("No tile provided to move action.")

        tile = kwargs["tile"]

        if not self.can_move:
            return False

        if self.moves_left <= 0:
            return False

        if not tile.is_occupied() and self.tile_is_occupiable(tile):
            self.tile = tile
            self.moves_left -= 1
            self.pos_x, self.pos_y, _ = tile.get_cords()
            if self.model is not None:
                self.model.setPos(LVector3(self.pos_x, self.pos_y, self.pos_z))
            return True

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

        self.register_unit(self)

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
            "name": get_i18n().lookup(self.name),
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
        if self.tag and self.tag in self.units_lookup:
            del self.units_lookup[self.tag]

        # Nullify references to break cyclic dependencies
        self.tile.units.remove_unit(self)

        if self.owner is not None:
            self.owner.units.remove_unit(self)

        self.owner = None
        self.actions.clear()
        self.tag = None
        return True

    @classmethod
    def register_unit(cls, unit: "UnitBaseClass") -> None:
        if unit.tag is None:
            raise ValueError(f"Unit {unit.key} has no tag")

        if unit.tag not in cls.units_lookup:
            cls.units_lookup[unit.tag] = unit

    @classmethod
    def get_unit_by_tag(cls, tag: str) -> Optional["UnitBaseClass"]:
        for unit in cls.units_lookup.values():
            if unit.tag == tag:
                return unit
        return None
