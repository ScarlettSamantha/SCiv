from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, Union
from weakref import ReferenceType
import weakref

from direct.showbase.DirectObject import DirectObject


from helpers.cache import Cache
from helpers.colors import Colors, Tuple4f
from helpers.placeholder import Placeholder
from managers.i18n import T_TranslationOrStrOrNone

if TYPE_CHECKING:
    from main import SCIV
    from gameplay.tile import Tile
    from gameplay.player import Player


class BaseEntity(ABC, DirectObject):
    name: T_TranslationOrStrOrNone = None
    description: T_TranslationOrStrOrNone = None

    icon: str | Path | None = Placeholder.getPlaceholderImagePathSmallIcon()
    icon_border_color: Tuple4f = Colors.YELLOW

    can_be_attacked: bool = False
    can_attack: bool = False
    can_defend: bool = False
    can_retaliate: bool = False
    can_move_after_attack: bool = False
    can_attack_indirectly: bool = False
    can_pillage: bool = False

    max_health: float = 100

    attack_power_mele: float = 0.0
    attack_power_ranged: float = 0.0
    attack_range: int = 1
    attack_armor_penetration: float = 0.0
    attack_points: float = 0.0
    attack_points_cost_mele: float = 0.0
    attack_points_cost_ranged: float = 0.0

    defense_mele: float = 0.0
    defense_ranged: float = 0.0

    def __init__(
        self,
        tile: Optional[Union["Tile", ReferenceType["Tile"]]] = None,
        owner: Optional["Player"] = None,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__()
        from gameplay.tile import Tile

        self.entity_key: Optional[str] = None
        self.entity_type_ref: Optional[str] = None
        self.is_registered: bool = False
        self.tile: Optional[ReferenceType["Tile"] | "Tile"] = weakref.ref(tile) if isinstance(tile, Tile) else None
        self.owner: Optional[Player] = owner

        self.attack_points_left: float = self.attack_points
        self.health_left: float = self.max_health

        if Cache.has_instance() is False:
            raise AssertionError("Cache instance is not set.")

        self.base: "SCIV" = Cache.get_showbase_instance()

    def get_tile(self) -> "Tile":
        if self.tile is None:
            raise ValueError("Tile is None")

        # Delay import so you don’t hit TYPE_CHECKING guard at module load
        from gameplay.tile import Tile

        # If it’s already a Tile instance, return it directly
        if isinstance(self.tile, Tile):
            return self.tile

        # If it’s a weakref to a Tile, dereference and return
        # Dereference self.tile directly as it's expected to be a ReferenceType

        tile_obj = self.tile()
        if tile_obj is None:
            raise ValueError("Tile reference is dead (None)")
        return tile_obj

    def set_tile(self, tile: "Tile") -> None:
        self.tile = weakref.ref(tile)

    def __getstate__(self) -> Dict[str, Any]:
        state = self.__dict__.copy()
        if "base" in state:
            del state["base"]
        return state

    def get_registered_status(self) -> bool:
        return self.is_registered

    @classmethod
    def get_attack_power_mele(cls) -> float:
        return cls.attack_power_mele

    @classmethod
    def get_attack_power_ranged(cls) -> float:
        return cls.attack_power_ranged

    @classmethod
    def get_attack_range(cls) -> int:
        return cls.attack_range

    @classmethod
    def get_attack_armor_penetration(cls) -> float:
        return cls.attack_armor_penetration

    @classmethod
    def get_defense_mele(cls) -> float:
        return cls.defense_mele

    @classmethod
    def get_defense_ranged(cls) -> float:
        return cls.defense_ranged

    @classmethod
    def get_max_health(cls) -> float:
        return cls.max_health

    def get_attack_points_left(self) -> float:
        return self.attack_points_left

    @classmethod
    def get_attack_points(cls) -> float:
        return cls.attack_points

    @classmethod
    def get_attack_points_cost_mele(cls) -> float:
        return cls.attack_points_cost_mele

    @classmethod
    def get_attack_points_cost_ranged(cls) -> float:
        return cls.attack_points_cost_ranged

    def destroy(self, as_system: bool = False) -> None: ...

    def kill(self) -> None:
        self.health_left = 0
        self.destroy()

    def health(self) -> float:
        return self.health_left

    def receive_damage(self, damage: float) -> bool:
        self.health_left -= damage
        if self.health_left <= 0:
            return True
        return False

    def get_owner(self) -> "Player":
        if self.owner is None:
            raise ValueError("Owner is None")
        return self.owner

    def get_pos(self) -> Tuple[float, float, float]:
        """
        Get the position of the entity in the world.
        """
        if self.tile is None:
            raise ValueError("Tile is None")
        if isinstance(self.tile, weakref.ReferenceType):
            tile = self.tile()
            if tile is None:
                raise ValueError("Tile reference is dead (None)")
        else:
            tile = self.tile
        return tile.get_pos()
