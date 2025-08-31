import random
from enum import Enum
from logging import Logger
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple, Type, Union, cast
from weakref import ReferenceType

from gameplay.condition import Conditions
from gameplay.exceptions.improvement_exceptions import ImprovementUpgradeException
from gameplay.yields import Yields
from helpers.cache import Cache, LogManager
from managers.entity import EntityType
from managers.i18n import T_TranslationOrStrOrNone
from system.effects import Effects
from system.entity import BaseEntity

if TYPE_CHECKING:
    from gameplay.player import Player
    from gameplay.resources.core.basic._base import BasicBaseResource
    from gameplay.tile import Tile
    from gameplay.unit import Unit


class ImprovementBuildTurnMode(Enum):
    SINGLE_TURN = 0
    MULTI_TURN_FIXED = 1
    MULTI_TURN_RESOURCE = 2


class Improvement(BaseEntity):
    name: T_TranslationOrStrOrNone
    description: T_TranslationOrStrOrNone
    _model: str | None = None
    _model_scale: float = 1.0
    _model_hpr: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    _model_default_offset: Tuple[float, float, float] = (0.0, 0.0, 0.001)  # to rise above the tile

    tile_yield_improvement: Yields = Yields.nullYield()
    maintenance_cost: Yields = Yields.nullYield()

    placeable_on_condition: Conditions | bool = True

    placeable_by_unit: Type["Unit"] | None = None

    placeable_by_player: bool = False
    placeable_on_tiles: bool = False
    placeable_on_city: bool = False

    visible_on_condition: Conditions | bool = True

    def __init__(
        self,
        key: Optional[str] = None,
        tile: "Tile | None" = None,
        owner: Optional[Union["Player", ReferenceType["Player"]]] = None,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(tile=tile, owner=owner, *args, **kwargs)
        from gameplay.resources.core.basic.production import Production

        self.tag = self.generate_tag()
        self.key: str = self.tag if key is None else key
        self.entity_key = self.key
        self.entity_type_ref = EntityType.IMPROVEMENT.value

        self.active: bool = True
        self.destroyed: bool = False

        self.upgradable: bool = False
        self.upgrade_into: Type[Improvement] | None = None
        self.upgrade_conditions: Conditions = Conditions()

        self.constructable_builder: bool = True
        self.constructable_on_tile: bool = True

        self.player_enabled: bool = True

        self.multi_turn_mode: ImprovementBuildTurnMode = ImprovementBuildTurnMode.SINGLE_TURN

        self.amount_resource_needed: Yields = Yields.nullYield()
        self.resource_needed: type[BasicBaseResource] = Production

        self.turns_needed: float | int | None = None
        self.build_progress: float | int | None = None

        self.effects: Effects = Effects(self)
        self.conditions: Conditions = Conditions()

        self._tile_yield_improvement: Yields = self.tile_yield_improvement
        self._maintenance_cost: Yields = self.maintenance_cost

        self._model_offset: Tuple[float, float, float] = self._model_default_offset

    def dump(self) -> Dict[str, Any]:
        state: Dict[str, Any] = self.__dict__.copy()
        state.pop("base", None)
        state.pop("_logger", None)
        state.pop("model", None)
        state["resource_needed"] = (
            f"{self.resource_needed.__module__}.{self.resource_needed.__name__}" if self.resource_needed else None
        )
        state["cls_ref"] = f"{self.__class__.__module__}.{self.__class__.__name__}"
        state["effects"] = self.effects.dump()
        state["_tile_yield_improvement"] = self._tile_yield_improvement.dump()
        state["tile_yield_improvement"] = self.tile_yield_improvement.dump()
        state["_maintenance_cost"] = self._maintenance_cost.dump()
        state["effects"] = self.effects.dump()
        state["owner"] = self.get_owner().get_tag()
        state["tile_tag"] = self.get_tile().get_tag() if self.get_tile() else None
        state["health_left"] = self.health_left if hasattr(self, "health_left") else 100
        return state

    def load_state(self) -> None:
        from gameplay.player import EntityManager, EntityType

        entity_manager: EntityManager = EntityManager.get_singleton_instance()

        self._logger: Logger = LogManager.get_singleton_instance().gameplay.getChild("improvement")
        self.base = Cache.get_showbase_instance()

        self._tile_yield_improvement = Yields.from_dict(getattr(self, "_tile_yield_improvement", {}))
        self.tile_yield_improvement = Yields.from_dict(getattr(self, "tile_yield_improvement", {}))
        self._maintenance_cost = Yields.from_dict(getattr(self, "_maintenance_cost", {}))

        self.owner = cast(
            ReferenceType["Player"],
            EntityManager.get_singleton_instance().get_ref_weak(EntityType.PLAYER, getattr(self, "owner", None)),  # type:ignore
        )
        self.tile = cast(ReferenceType["Tile"], entity_manager.get_ref_weak(EntityType.TILE, getattr(self, "tile_tag")))  # type:ignore

        resource_needed_class = getattr(self, "resource_needed", None)
        if resource_needed_class is None:
            from gameplay.resources.core.basic.production import Production

            self.resource_needed = Production
        else:
            self.resource_needed = EntityManager.get_singleton_instance().dynamic_import(resource_needed_class)

        self.amount_resource_needed = Yields.from_dict(getattr(self, "amount_resource_needed", {}))

        effects = Effects(self)
        effects.load_state(self.effects)  # type:ignore
        self.effects = effects

        self._health_left = getattr(self, "health_left", getattr(self, "max_health", 100))

    def get_maintenance_cost(self) -> Yields:
        return self._maintenance_cost

    @classmethod
    def on_tooltip(cls) -> str:
        tile_yield_improvement = cls.tile_yield_improvement.props(only_non_nul=True)
        tile_yield_improvement = ", ".join(
            f"[{str(value.name)[0]}: {'+' if value.value > 0 else ''}{value.value}]"
            for value in tile_yield_improvement.values()
        )
        maintenance_cost = cls.maintenance_cost.props(only_non_nul=True)
        maintenance_cost = ", ".join(f"{value.name}: {value.value}" for value in maintenance_cost.values())

        return (
            str(cls.name)
            + "\n\n"
            + str(cls.description)
            + "\n\n"
            + "Yield Improvement: "
            + tile_yield_improvement
            + "\n\n"
            + "Maintenance Cost: "
            + maintenance_cost
        )

    def register(self):
        from managers.entity import EntityManager, EntityType

        if self.is_registered is True:
            return

        EntityManager.get_singleton_instance().register(entity=self, type=EntityType.IMPROVEMENT, key=self.tag)

    def unregister(self):
        from managers.entity import EntityManager, EntityType

        EntityManager.get_singleton_instance().unregister(entity=self, type=EntityType.IMPROVEMENT)

    def _validate_state(self) -> bool:
        return True

    def generate_tag(self) -> str:
        if self.tile is None:
            return f"improvement_{self.name}_{random.randrange(0, 10000)}"
        else:
            return f"improvement_{self.get_tile().x}_{self.get_tile().y}_{str(self.name)}_{random.randrange(0, 1000)}"

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value: str):
        self._model = value

    @property
    def tile_yield(self) -> Yields:
        return self._tile_yield_improvement

    @tile_yield.setter
    def tile_yield(self, value: Yields) -> None:
        self._tile_yield_improvement = value

    def set_price_free(self):
        self.amount_resource_needed = Yields.nullYield()

    def on_construct(self):
        if self.tile is None:
            raise ValueError("Tile is not set for the improvement")

        if self.is_registered is False:
            self.register()

    def on_destroy(self):
        if self.is_registered is True:
            self.unregister()

        for effect in self.effects.get_effects().values():
            effect.on_deactivate()

    def on_remove(self):
        if self.is_registered is True:
            self.unregister()

    def upgrade(self):
        if self.upgrade_into is None:
            raise ImprovementUpgradeException("Cant upgrade into a null object. needs to be an improvement effect")
        self.replace(self.upgrade_into)

    def replace(self, _with: Type["Improvement"]):
        pass

    def get_model_path(self) -> str | None:
        return self._model

    def on_turn_end(self, turn: int):
        self.effects.on_turn_end(turn)

    def get_model_hpr(self) -> Tuple[float, float, float]:
        return self._model_hpr

    def get_model_scale(self) -> float:
        return self._model_scale

    def get_model_offset(self) -> Tuple[float, float, float]:
        return self._model_offset

    @staticmethod
    def basic_resource_improvement(
        name: str,
        tile: "Tile",
        property: str,
        delta: float,
        mode: int = Yields.ADDITIVE,
        health: int = 100,
    ) -> "Improvement":
        ref = Improvement(key=name, name=name, tile=tile, health=health)
        _yield = Yields(f"{name} yield")
        _yield.mode = mode
        _yield.set_prop(property, delta)
        ref.tile_yield = _yield
        return ref

    def on_inspect(self):
        data = {
            "name": str(self.name),
            "description": str(self.description),
            "tile_yield_improvement": self.tile_yield_improvement.on_inspect(basic=True),
            "maintenance_cost": self.maintenance_cost.on_inspect(basic=True),
            "placeable_on_condition": self.placeable_on_condition,
            "placeable_by_unit": self.placeable_by_unit,
            "placeable_by_player": self.placeable_by_player,
            "placeable_on_tiles": self.placeable_on_tiles,
            "placeable_on_city": self.placeable_on_city,
            "visible_on_condition": self.visible_on_condition,
        }

        return data, self.get_children_inspect()

    def get_children_inspect(self) -> Dict[str, Set[Any] | List[Any]]:
        return {
            "effects": set(self.effects.get_effects().values()),
        }

    def get_tile_yield(self) -> Yields:
        return self.tile_yield
