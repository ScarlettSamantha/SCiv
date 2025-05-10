from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Union
from weakref import ReferenceType

from direct.showbase.DirectObject import DirectObject


from gameplay.player import Player
from helpers.cache import Cache
from helpers.colors import Colors, Tuple4f
from helpers.placeholder import Placeholder
from managers.i18n import T_TranslationOrStrOrNone

if TYPE_CHECKING:
    from main import SCIV
    from gameplay.tiles.base_tile import BaseTile


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
        tile: Optional[Union["BaseTile", ReferenceType["BaseTile"]]] = None,
        owner: Optional[Player] = None,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__()
        self.entity_key: Optional[str] = None
        self.entity_type_ref: Optional[str] = None
        self.is_registered: bool = False
        self.tile: Optional[Union["BaseTile", ReferenceType["BaseTile"]]] = tile
        self.owner: Optional[Player] = owner

        self.attack_points_left: float = self.attack_points
        self.health_left: float = self.max_health

        if Cache.has_instance() is False:
            raise AssertionError("Cache instance is not set.")

        self.base: "SCIV" = Cache.get_showbase_instance()

    def get_tile(self) -> "BaseTile":
        if self.tile is None:
            raise ValueError("Tile is None")

        # Delay import so you don’t hit TYPE_CHECKING guard at module load
        from gameplay.tiles.base_tile import BaseTile

        # If it’s already a BaseTile instance, return it directly
        if isinstance(self.tile, BaseTile):
            return self.tile

        # If it’s a weakref to a BaseTile, dereference and return
        # Dereference self.tile directly as it's expected to be a ReferenceType
        tile_obj = self.tile()
        if not isinstance(tile_obj, BaseTile):
            raise TypeError(f"Reference resolved to unexpected type {type(tile_obj)}")
        return tile_obj

    def set_tile(self, tile: "BaseTile") -> None:
        self.tile = tile

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

    def destroy(self, as_system: bool = False) -> None:
        """Placeholder destroy method."""
        pass

    def kill(self) -> None:
        self.health_left = 0
        self.destroy()

    def health(self) -> float:
        return self.health_left

    def receive_damage(self, damage: float) -> bool:
        self.health_left -= damage
        if self.health_left <= 0:
            self.kill()
            return True
        return False

    def get_owner(self) -> Optional[Player]:
        return self.owner
