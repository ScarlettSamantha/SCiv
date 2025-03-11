from enum import Enum
from typing import TYPE_CHECKING, Callable, Optional, Tuple, Type

from gameplay.condition import Conditions
from gameplay.effect import Effects
from gameplay.exceptions.improvement_exceptions import ImprovementUpgradeException
from gameplay.player import Player
from gameplay.resources.core.basic._base import BasicBaseResource
from gameplay.resources.core.basic.production import Production
from gameplay.tile_yield import TileYield
from managers.i18n import T_TranslationOrStr, T_TranslationOrStrOrNone
from mixins.callbacks import CallbacksMixin
from system.entity import BaseEntity

if TYPE_CHECKING:
    from gameplay.tiles.base_tile import BaseTile


class ImprovementBuildTurnMode(Enum):
    SINGLE_TURN = 0
    MULTI_TURN_FIXED = 1
    MULTI_TURN_RESOURCE = 2


class Improvement(CallbacksMixin, BaseEntity):
    name: T_TranslationOrStr
    description: T_TranslationOrStrOrNone
    _model = None

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        CallbacksMixin.__init__(self, *args, **kwargs)

        self.active: bool = True
        self.destroyed: bool = False

        self.health: int = 100
        self.max_health: int = 100

        self.upgradable: bool = False
        self.upgrade_into: Type[Improvement] | None = None
        self.upgrade_conditions: Conditions = Conditions()

        self.constructable_builder: bool = True
        self.constructable_on_tile: bool = True

        self.placeable_by_player: bool = False
        self.placeable_on_tiles: bool = False
        self.placeable_on_city: bool = False
        self.placeable_on_condition: Conditions | bool = False

        self.player_enabled: bool = True

        self.multi_turn_mode: ImprovementBuildTurnMode = ImprovementBuildTurnMode.SINGLE_TURN
        self.tile: Optional[BaseTile] = None

        # Following 3 are not needed in single turn mode.
        self.amount_resource_needed: TileYield = TileYield.nullYield()
        self.resource_needed: type[BasicBaseResource] = Production

        # Dynamic value, will be set by the game.
        self.turns_needed: float | int | None = None
        self.build_progress: float | int | None = None

        self.tile_yield_improvement: TileYield = TileYield.nullYield()
        self.effects: Effects = Effects()
        self.conditions: Conditions = Conditions()

        self.maintenance_cost: TileYield = TileYield.nullYield()

        self._model_offset: Tuple[int, int, int] = (
            0,
            0,
            0,
        )  # This is not static due to the fact that the model can be rotated. and moved on the tile itself.
        self.owner: Optional[Player] = None

    def _validate_state(self) -> bool:
        return True

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value):
        self._model = value

    @property
    def tile_ref(self):
        return self._tile_ref

    @tile_ref.setter
    def tile_ref(self, value):
        self._tile_ref = value

    @property
    def tile_yield(self) -> TileYield:
        return self._tile_yield_improvement

    @tile_yield.setter
    def tile_yield(self, value: TileYield) -> None:
        if not isinstance(value, TileYield):
            raise TypeError(f"Tileyield cannot be type {type(value)}")
        self._tile_yield_improvement = value

    def set_price_free(self):
        self.amount_resource_needed = TileYield.nullYield()

    def on_construct(self, callback: Callable):
        self.register_callback("on_construct", callback)

    def trigger_on_construct(self):
        self.trigger_callback("on_construct")

    def on_destroy(self, callback: Callable):
        self.register_callback("on_destory", callback)

    def trigger_on_destory(self):
        self.trigger_callback("on_destroy")

    def on_remove(self, callback: Callable):
        self.register_callback("on_remove", callback)

    def trigger_on_remove(self):
        self.trigger_callback("on_remove")

    def upgrade(self):
        if self.upgrade_into is None:
            raise ImprovementUpgradeException("Cant upgrade into a null object. needs to be an improvement effect")
        self.replace(self.upgrade_into)

    def replace(self, _with: Type["Improvement"]):
        pass

    def set_tile(self, tile: "BaseTile"):
        self.tile = tile

    def get_tile(self) -> "BaseTile | None":
        return self.tile

    def set_owner(self, owner: Player):
        self.owner = owner

    def get_owner(self) -> Player | None:
        return self.owner

    @staticmethod
    def basic_resource_improvement(
        name: str,
        tile: "BaseTile",
        property: str,
        delta: float,
        mode: int = TileYield.ADDITIVE,
        health: int = 100,
    ) -> "Improvement":
        ref = Improvement(key=name, name=name, tile=tile, health=health)
        _yield = TileYield(f"{name} yield")
        _yield.mode = mode
        _yield.set_prop(property, delta)
        ref.tile_yield = _yield
        return ref
