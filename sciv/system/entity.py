import weakref
from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple, Union, cast
from uuid import uuid4
from weakref import ReferenceType

from direct.showbase.DirectObject import DirectObject
from helpers.cache import Cache
from helpers.colors import Colors, Tuple4f
from helpers.placeholder import Placeholder
from managers.i18n import T_TranslationOrStrOrNone
from mixins.inspectable import Inspectable

if TYPE_CHECKING:
    from gameplay.effect import Effect
    from gameplay.player import Player
    from gameplay.tile import Tile

    from sciv.game import OpenCiv


class BaseEntity(ABC, DirectObject, Inspectable):
    name: T_TranslationOrStrOrNone = None
    description: T_TranslationOrStrOrNone = None

    icon: str | Path | None = Placeholder.getPlaceholderImagePathSmallIcon()
    icon_border_color: Tuple4f = Colors.YELLOW

    can_be_attacked: bool = False
    can_attack: bool = False
    can_defend: bool = False
    can_retaliate: bool = True
    can_move_after_attack: bool = False
    can_attack_indirectly: bool = False
    can_pillage: bool = False

    max_health: float = 100

    attack_power_mele: float = 0.0
    attack_power_ranged: float = 0.0
    attack_range: int = 1
    attack_armor_penetration: float = 0.0
    attack_points: float = 0.0
    attack_points_cost_mele: float = 1.0
    attack_points_cost_ranged: float = 1.0

    defense_mele: float = 1.0
    defense_ranged: float = 1.0

    def __init__(
        self,
        tile: Optional[Union["Tile", ReferenceType["Tile"]]] = None,
        owner: Optional[Union["Player", ReferenceType["Player"]]] = None,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__()
        Inspectable.__init__(self, *args, **kwargs)
        from gameplay.tile import Tile

        self.tag: str = str(uuid4().hex)
        self.entity_key: Optional[str] = None
        self.entity_type_ref: Optional[str] = None
        self.is_registered: bool = False
        self.tile: Optional[ReferenceType["Tile"] | "Tile"] = weakref.ref(tile) if isinstance(tile, Tile) else None

        if tile is None:
            self.tile_tag: str | None = None
        else:
            self.tile_tag: str | None = tile.get_tag() if isinstance(tile, Tile) else tile().get_tag()  # type: ignore

        self.attack_points_left: float = self.attack_points
        self._health_left: float = self.max_health

        self._owner: Optional[ReferenceType["Player"]] = (
            owner if isinstance(owner, weakref.ReferenceType) or owner is None else weakref.ref(owner)
        )

        if owner is not None:
            if isinstance(owner, weakref.ReferenceType):
                owner_instance = owner()
                if owner_instance is None:
                    raise ValueError("Owner reference is dead (None)")
                self.owner_tag: str = owner_instance.get_tag()
            else:
                self.owner_tag = owner.get_tag()

        self._is_alive: bool = True

        if Cache.has_instance() is False:
            raise AssertionError("Cache instance is not set.")

        self.base: "OpenCiv" = Cache.get_showbase_instance()

    @property
    def health_left(self) -> float:
        return self._health_left

    @health_left.setter
    def health_left(self, value: float) -> None:
        if value < 0:
            value = 0
        self._health_left = value
        if self._health_left <= 0:
            self._is_alive = False
            self.kill()

    @property
    def owner(self) -> Optional[Union[ReferenceType["Player"], "Player"]]:
        if isinstance(self._owner, weakref.ReferenceType):
            owner = self._owner()
            if owner is None:
                raise ValueError("Owner reference is dead (None)")
            return owner
        return self._owner

    @owner.setter
    def owner(self, value: Optional[Union["Player", ReferenceType["Player"]]]) -> None:
        if value is None:
            self._owner = None
        elif isinstance(value, weakref.ReferenceType):
            self._owner = value
        else:
            self._owner = weakref.ref(value)

    def get_tile(self) -> "Tile":
        from gameplay.tile import Tile

        if isinstance(self, Tile):
            return self

        if self.tile is None:
            raise ValueError("Tile is None")

        if isinstance(self.tile, Tile):
            return self.tile

        if (tile_obj := self.tile()) is None:
            raise ValueError("Tile reference is dead (None)")
        return tile_obj

    def set_tile(self, tile: "Tile") -> None:
        self.tile = weakref.ref(tile)

    def __getstate__(self) -> Dict[str, Any]:
        state = self.__dict__.copy()
        if "base" in state:
            del state["base"]
        if "_logger" in state:
            del state["_logger"]

        if "_owner" in state:
            if isinstance(self._owner, weakref.ReferenceType):
                owner: Player | None = self._owner()
                if owner is not None:
                    state["owner_tag"] = (
                        owner.get_tag()
                    )  # last minute refresh of owner tag to make sure it is up to date

            del state["_owner"]

        if "tile" in state:
            if isinstance(self.tile, weakref.ReferenceType):
                tile: Tile | None = self.tile()
                if tile is not None:
                    state["tile_tag"] = tile.get_tag()

            del state["tile"]
        state["_cls"] = f"{self.__class__.__module__}.{self.__class__.__name__}"

        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        from managers.entity import EntityManager, EntityType
        from managers.log import LogManager

        self.base: "OpenCiv" = Cache.get_showbase_instance()
        self._logger = LogManager.get_singleton_instance().gameplay.getChild("entity")

        if "tile_tag" in state:
            if (tile_tag := state.get("tile_tag")) is not None:
                self.tile = cast(
                    ReferenceType["Tile"] | None,
                    EntityManager.get_singleton_instance().get_ref(key=tile_tag, type=EntityType.TILE, weak_ref=True),
                )
        else:
            self.tile = None

        if "owner_tag" in state:
            if (owner_tag := state.get("owner_tag")) is not None:
                self._owner = cast(
                    ReferenceType["Player"] | None,
                    EntityManager.get_singleton_instance().get_ref(
                        key=owner_tag, type=EntityType.PLAYER, weak_ref=True
                    ),
                )
                if self._owner is None:
                    self._logger.warning(f"Owner with tag {owner_tag} not found, setting owner to None.")
        else:
            self._owner = None

        self.__dict__.update(state)

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

    def is_alive(self) -> bool:
        return self.health() > 0

    def on_inspect(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        if not self._is_alive:
            return {
                "error": "This entity is not alive, its a phantom. this is a bug, please trace where it does not get destroyed properly.",
            }, {}

        return {
            "key": self.entity_key,
            "tag": self.tag,
            "name": self.name,
            "description": self.description,
            "health_left": self.health_left,
            "max_health": self.max_health,
            "tile": self.get_tile().get_pos() if self.tile else None,
            "owner": self.get_owner().name if self.owner else None,
        }, self.get_children_inspect()

    def get_children_inspect(self) -> Dict[str, Set[Any] | List[Any]]: ...

    def destroy(self, as_system: bool = False) -> None: ...

    def kill(self) -> None:
        self._health_left = 0
        self.destroy()

    def health(self) -> float:
        return self.health_left

    def receive_damage(self, damage: float) -> bool:
        self.health_left -= damage
        if self.health_left <= 0:
            return True
        return False

    def heal(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("Heal amount cannot be negative")
        self.health_left += amount
        if self.health_left > self.max_health:
            self.health_left = self.max_health

    def get_owner(self) -> "Player":
        if self.owner is None:
            assert self.owner_tag is not None, "Owner tag is not set"
            from managers.entity import EntityManager, EntityType

            owner = cast(
                "ReferenceType[Player] | None",
                EntityManager.get_singleton_instance().get_ref(
                    key=self.owner_tag, type=EntityType.PLAYER, weak_ref=True
                ),
            )
            if owner is None:
                raise ValueError(f"Owner with tag {self.owner_tag} not found")

            self._owner = owner

            return owner()  # type: ignore

        if isinstance(self.owner, weakref.ReferenceType):
            owner = self.owner()
            if owner is None:
                raise ValueError("Owner reference is dead (None)")
            return owner

        return self.owner

    def set_owner(self, owner: Optional[Union["Player", weakref.ReferenceType["Player"]]] = None) -> None:
        from gameplay.player import Player

        if isinstance(owner, Player):
            self.owner = weakref.ref(owner)
            return
        self.owner = owner

    def get_pos(self) -> Tuple[float, float, float]:
        if self.tile is None:
            raise ValueError("Tile is None")
        if isinstance(self.tile, weakref.ReferenceType):
            tile = self.tile()
            if tile is None:
                raise ValueError("Tile reference is dead (None)")
        else:
            tile = self.tile
        return tile.get_pos()

    def get_tag(self) -> str:
        assert self.tag is not None, "Tag is not set"
        return self.tag

    def get_entity_type(self) -> str:
        assert self.entity_type_ref is not None, "Entity type reference is not set"
        return self.entity_type_ref

    def get_distance_to(self, other: "BaseEntity") -> float:
        from gameplay.repositories.tile import TileRepository

        if self.tile is None:
            raise ValueError("Tile is None")

        if isinstance(self.tile, weakref.ReferenceType):
            tile: Tile | None = self.tile()
            if tile is None:
                raise ValueError("Tile reference is dead (None)")
        else:
            tile = self.tile

        if other.tile is None:
            raise ValueError("Other entity's tile is None")

        if isinstance(other.tile, weakref.ReferenceType):
            other_tile: Tile | None = other.tile()
            if other_tile is None:
                raise ValueError("Other entity's tile reference is dead (None)")
        else:
            other_tile = other.tile

        return TileRepository.distance(tile, other_tile)

    def add_effect(self, effect: "Effect", execute_on_add: bool = False) -> None:
        from system.effects import Effects

        if not hasattr(self, "effects"):
            raise ValueError("This entity does not support effects")
        assert isinstance(self.effects, Effects), "Effects attribute is not of type Effects"  # type: ignore
        effects: Effects = self.effects  # type: ignore
        effects.add_effect(effect, execute_on_add=execute_on_add)

    def remove_effect(self, effect: "Effect") -> None:
        from system.effects import Effects

        if not hasattr(effect, "effects"):
            raise ValueError("This entity does not support effects")

        assert isinstance(self.effects, Effects), "Effects attribute is not of type Effects"  # type: ignore
        effects: Effects = self.effects  # type: ignore
        effects.remove_effect(effect)
