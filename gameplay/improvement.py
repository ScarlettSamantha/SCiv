import random
import uuid
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Tuple, Type

from gameplay.condition import Conditions
from gameplay.exceptions.improvement_exceptions import ImprovementUpgradeException

from gameplay.yields import Yields
from managers.entity import EntityManager, EntityType
from managers.i18n import T_TranslationOrStrOrNone
from system.effects import Effects
from system.entity import BaseEntity

if TYPE_CHECKING:
    from gameplay.player import Player
    from gameplay.resources.core.basic._base import BasicBaseResource
    from gameplay.tiles.base_tile import BaseTile
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
    _model_default_offset: Tuple[float, float, float] = (0.0, 0.0, 0.09)  # to rise above the tile

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
        tile: "BaseTile | None" = None,
        owner: Optional["Player"] = None,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(tile, owner, *args, **kwargs)
        from gameplay.resources.core.basic.production import Production

        self.key: str = key if key else uuid.uuid4().hex
        self.active: bool = True
        self.destroyed: bool = False

        self.upgradable: bool = False
        self.upgrade_into: Type[Improvement] | None = None
        self.upgrade_conditions: Conditions = Conditions()

        self.constructable_builder: bool = True
        self.constructable_on_tile: bool = True

        self.player_enabled: bool = True

        self.multi_turn_mode: ImprovementBuildTurnMode = ImprovementBuildTurnMode.SINGLE_TURN

        # Following 3 are not needed in single turn mode.
        self.amount_resource_needed: Yields = Yields.nullYield()
        self.resource_needed: type[BasicBaseResource] = Production

        # Dynamic value, will be set by the game.
        self.turns_needed: float | int | None = None
        self.build_progress: float | int | None = None

        self.effects: Effects = Effects(self)
        self.conditions: Conditions = Conditions()

        # This will be applied when the resource is placed on the tile.
        self._tile_yield_improvement: Yields = self.tile_yield_improvement
        self._maintenance_cost: Yields = self.maintenance_cost

        self._model_offset: Tuple[float, float, float] = self._model_default_offset

        self.owner: Optional["Player"] = None
        self.tag: str = ""

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

    def __del__(self):
        if self.is_registered is True:
            self.unregister()

    def register(self):
        if self.is_registered is True:
            return
        EntityManager.get_singleton_instance().register(entity=self, type=EntityType.IMPROVEMENT, key=self.tag)

    def unregister(self):
        EntityManager.get_singleton_instance().unregister(entity=self, type=EntityType.IMPROVEMENT)

    def _validate_state(self) -> bool:
        return True

    def generate_tag(self):
        if self.tile is None:
            self.tag = f"improvement_{self.name}_{random.randrange(0, 10000)}"
        else:
            self.tag = f"improvement_{self.get_tile().x}_{self.get_tile().y}_{self.name}_{random.randrange(0, 10000)}"

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
            self.generate_tag()
            self.register()

        for effect in self.effects.get_effects().values():
            effect.apply(self.get_tile())

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

    def set_owner(self, owner: "Player"):
        self.owner = owner

    def get_owner(self) -> "Player | None":
        return self.owner

    def on_turn_end(self, turn: int):
        self.effects.on_turn_end(turn)

    @staticmethod
    def basic_resource_improvement(
        name: str,
        tile: "BaseTile",
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
