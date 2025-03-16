from typing import Type

from direct.showbase import MessengerGlobal

from gameplay.actions.unit.base_unit_action import BaseUnitAction
from gameplay.improvement import Improvement
from gameplay.rules import get_game_rules
from gameplay.tiles.base_tile import BaseTile, CantBuildReason
from gameplay.units.unit_base import UnitBaseClass
from managers.i18n import t_
from system.actions import Action


class BuildAction(BaseUnitAction):
    def __init__(self, improvement: Type[Improvement], unit: UnitBaseClass):
        self.unit: UnitBaseClass = unit

        if self.unit.tile is None:
            raise ValueError("Unit has no tile")

        self.tile: BaseTile = self.unit.tile
        self._condition_result: bool | CantBuildReason = False
        self.improvement: Type[Improvement] = improvement
        super().__init__(
            name=t_("actions.unit.move"),
            action=self.build_wrapper,
            condition=self.can_build,
            on_failure=self.on_fail,
            on_success=self.on_success,
        )

        self.on_the_spot_action = True
        self.targeting_tile_action = False
        self.get_return_as_failure_argument = True

        self.unit_looses_movement_after_building_rule: bool = (
            get_game_rules().get_unit_looses_movement_after_building_rule()
        )

    def build_wrapper(self, *args, **kwargs) -> CantBuildReason | bool:
        building: Improvement = self.improvement(self.tile)
        result = self.tile.build(building)
        self._result = result
        return result

    def can_build(self, *args, **kwargs) -> bool:
        if len(self.tile.improvements()) > 0:
            MessengerGlobal.messenger.send(
                "ui.request.open.popup",
                [
                    "error",
                    t_("ui.dialogs.unit.build_improvement.improvement_already_exists.title"),
                    t_("ui.dialogs.unit.build_improvement.improvement_already_exists.message"),
                ],
            )
            self._condition_result = CantBuildReason.IMPROVEMENT_ALREADY_EXISTS
            return False
        if self.tile.is_passable() is False:
            MessengerGlobal.messenger.send(
                "ui.request.open.popup",
                [
                    "error",
                    t_("ui.dialogs.unit.build_improvement.improvement_not_passable.title"),
                    t_("ui.dialogs.unit.build_improvement.improvement_not_passable.message"),
                ],
            )
            self._condition_result = CantBuildReason.IMPROVEMENT_TILE_NOT_PASSABLE
            return False
        if self.unit.can_build is False:
            MessengerGlobal.messenger.send(
                "ui.request.open.popup",
                [
                    "error",
                    t_("ui.dialogs.unit.build_improvement.unit_cant_build.title"),
                    t_("ui.dialogs.unit.build_improvement.unit_cant_build.message"),
                ],
            )
            self._condition_result = CantBuildReason.NOT_CONSTRUCTABLE_BUILDER
            return False
        if self.unit.owner != self.tile.owner:
            MessengerGlobal.messenger.send(
                "ui.request.open.popup",
                [
                    "error",
                    t_("ui.dialogs.unit.build_improvement.improvement_not_owned.title"),
                    t_("ui.dialogs.unit.build_improvement.improvement_not_owned.message"),
                ],
            )
            self._condition_result = CantBuildReason.NOT_PLACEABLE_UPON_ENEMEY_TILE
            return False
        return self.unit.can_build

    def on_success(self, *args, **kwargs):
        MessengerGlobal.messenger.send("game.gameplay.unit.build_improvement_success", [self.improvement, self.unit])
        if self.unit_looses_movement_after_building_rule:
            self.unit.drain_movement_points(None)  # Will set the unit to 0 movement points.

        if self.unit.build_charges != 0:
            self.unit.build_charges_left -= 1

        if self.unit.build_charges_left == 0:
            self.unit.destroy()

    def on_fail(self, action: Action, *args, **kwargs):
        result = action.get_result()
        MessengerGlobal.messenger.send(
            "game.gameplay.unit.build_improvement_failure", [result, self.improvement, self.unit]
        )
