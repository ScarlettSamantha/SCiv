from typing import Any

from direct.showbase.MessengerGlobal import messenger

from direct.showbase import MessengerGlobal
from gameplay.actions.unit.base_unit_action import BaseUnitAction
from gameplay.tile import Tile
from gameplay.unit import Unit
from managers.combat import T_TARGET, CombatOutcome, CombatResults
from managers.i18n import t_
from system.actions import Action


class AttackAction(BaseUnitAction):
    def __init__(self, instance: Unit):
        self.unit = instance
        super().__init__(
            name=t_("actions.unit.attack"),
            action=self.attack_wrapper,
            condition=instance.can_attack,
            on_success=self.success,
            on_failure=self.attack_failure_popup,
            success_condition=self.is_action_successful,
        )

        self.on_the_spot_action = False
        self.targeting_tile_action = False
        self.targeting_unit_action = True
        self.get_return_as_failure_argument = True
        self.keep_targeting_after_use = True

    def attack_wrapper(self, _: Action, executor: T_TARGET, target: T_TARGET) -> CombatOutcome:
        if isinstance(executor, Unit) and not isinstance(target, Tile):
            outcome = executor.attack(target)
            self._result = outcome
            return outcome
        else:
            raise TypeError(f"Executor of type {type(executor).__name__} does not support 'attack'")

    def is_action_successful(self, _: Action, *args: Any, **kwargs: Any) -> bool:
        result = self.get_result()
        if result is None:
            return False

        if not isinstance(result, CombatOutcome):
            raise TypeError(f"Expected CombatOutcome, got {type(result).__name__}")

        if result.status in (CombatResults.DEFENDER_KILLED, CombatResults.DEFENDER_DAMAGED):
            return True

        return False

    def success(self, *args: Any, **kwargs: Any):
        messenger.send("unit.action.attack.success", [self.get_result()])
        result = self.get_result()
        if result is None or not isinstance(result, CombatOutcome):
            raise TypeError(f"Expected CombatOutcome, got {type(result).__name__}")

        if result.status == CombatResults.DEFENDER_KILLED:
            MessengerGlobal.messenger.send(
                "ui.request.open.popup",
                [
                    "unit_attack_success",
                    t_("ui.dialogs.unit.combat.attack_success.title"),
                    t_("ui.dialogs.unit.combat.attack_success.message"),
                ],
            )

    def attack_failure_popup(self, action: Action, *args: Any, **kwargs: Any):
        result = action.get_result()

        if not isinstance(result, CombatOutcome):
            raise TypeError(f"Expected CombatOutcome, got {type(result).__name__}")

        text, description = "", ""

        if result.status == CombatResults.ATTACKER_KILLED:
            text, description = (
                t_("ui.dialogs.unit.combat.attack_errors.attacker_killed.title"),
                t_("ui.dialogs.unit.combat.attack_errors.attacker_killed.message"),
            )
        elif result.status == CombatResults.OWN_UNIT_ATTACK_DISABLED:
            text, description = (
                t_("ui.dialogs.unit.combat.attack_errors.own_unit_attack_disabled.title"),
                t_("ui.dialogs.unit.combat.attack_errors.own_unit_attack_disabled.message"),
            )
        elif result.status == CombatResults.NO_MOVEMENT:
            text, description = (
                t_("ui.dialogs.unit.combat.attack_errors.no_movement.title"),
                t_("ui.dialogs.unit.combat.attack_errors.no_movement.message"),
            )
        elif result.status == CombatResults.NO_POINTS:
            text, description = (
                t_("ui.dialogs.unit.combat.attack_errors.no_points.title"),
                t_("ui.dialogs.unit.combat.attack_errors.no_points.message"),
            )
        elif result.status == CombatResults.NO_RANGE:
            text, description = (
                t_("ui.dialogs.unit.combat.attack_errors.no_range.title"),
                t_("ui.dialogs.unit.combat.attack_errors.no_range.message"),
            )

        MessengerGlobal.messenger.send(
            "ui.request.open.popup",
            ["unit_attack_error", text, description],
        )
