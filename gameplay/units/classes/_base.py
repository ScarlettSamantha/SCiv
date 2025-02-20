import random
from direct.showbase.ShowBase import ShowBase
from panda3d.core import NodePath, LVector3, CollisionNode, BitMask32
from direct.showbase.Loader import Loader
from panda3d.core import CollisionCapsule

from managers.i18n import T_TranslationOrStr, Translation, get_i18n
from typing import Dict, Optional, Tuple, Type, Any, TYPE_CHECKING
from gameplay.combat.stats import Stats

if TYPE_CHECKING:
    from data.tiles.tile import Tile
    from gameplay.promotion import PromotionTree
    from gameplay.player import Player


class UnitBaseClass:
    units_lookup: Dict[str, "UnitBaseClass"] = {}

    def __init__(
        self,
        key: str,
        name: T_TranslationOrStr,
        description: T_TranslationOrStr,
        base: ShowBase,
        icon: str | None,
        promotion_tree: Type["PromotionTree"],
        owner: Optional["Player"] = None,
        tile: Optional["Tile"] = None,
        model: Optional[T_TranslationOrStr] = None,
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
        self.tile: Tile | None = tile  # Tile must be set before spawning
        self.model: Optional[NodePath | T_TranslationOrStr] = (
            model  # Will hold the Panda3D model
        )
        self.model_size: float = model_size  # Default size of the model
        self.model_rotation: Tuple[float, float, float] = (
            model_rotation  # Default rotation of the model
        )
        self.model_position_offset: Tuple[float, float, float] = model_position_offset
        self.base: ShowBase = base
        self.collides: bool = True
        self.tag: Optional[str] = None

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

        self.max_moves: int = 1
        self.moves_left: int = 1

        self.can_swim: bool = False
        self.can_fly: bool = False

        self.can_move: bool = True
        self.can_attack: bool = True
        self.can_heal: bool = True
        self.can_pillage: bool = True

    def spawn(self) -> bool:
        """
        Spawns the unit at its assigned tile, loading the model into Panda3D.
        Returns True if successful, False otherwise.
        """
        if self.tile is None:
            raise ValueError(f"Unit {self.key} cannot spawn without an assigned tile.")

        if not self.tile.is_occupied():  # Assumed tile method
            raise ValueError(f"Tile at {self.tile.get_cords()} is not passable.")

        if not isinstance(self.model, str):
            raise ValueError(f"Unit {self.key} has no model assigned.")

        # Load the Panda3D model and position it at the tile
        self.model = self.load_model(self.model)

        if not self.model:
            raise RuntimeError(f"Failed to load model for unit {self.key}")

        print(
            f"Unit {self.key} spawned at {self.tile.get_cords()} with model {self.model}"
        )
        return True

    def load_model(self, model_path: str) -> NodePath | None:
        """
        Loads the unit model in Panda3D, places it at the correct position,
        and automatically loads its collision geometry (if available).
        """
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

    def set_color(self, color: Tuple[float, float, float, float]) -> None:
        """
        Sets the color of the unit model.

        Args:
            color (Tuple[float, float, float, float]): The color to set.
        """
        if isinstance(self.model, str):
            raise ValueError(f"Unit {self.key} has no model assigned.")

        self.model.setColor(*color)

    def to_gui(self) -> Dict[str, Any]:
        return {
            "tag": self.tag,
            "key": self.key,
            "name": get_i18n().lookup(self.name),
            "description": self.description,
            "owner": self.owner.name,
            "cords": f"{round(self.pos_x, 5)}, {round(self.pos_y, 5)}, {round(self.pos_z, 5)}",
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

    @classmethod
    def register_unit(cls, unit: "UnitBaseClass") -> None:
        """
        Registers a unit type with the unit lookup table.

        Args:
            unit (UnitBaseClass): The unit to register.
        """
        if unit.tag is None:
            raise ValueError(f"Unit {unit.key} has no tag")

        if unit.tag not in cls.units_lookup:
            cls.units_lookup[unit.tag] = unit

    @classmethod
    def get_unit_by_tag(cls, tag: str) -> Optional["UnitBaseClass"]:
        """
        Retrieves a unit instance based on the provided tag.

        Args:
            tag (str): The tag associated with the unit.

        Returns:
            UnitBaseClass: The matching unit instance if found; otherwise, None.
        """
        for unit in cls.units_lookup.values():
            if unit.tag == tag:
                return unit
        return None
