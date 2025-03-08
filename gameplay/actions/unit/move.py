from direct.showbase.MessengerGlobal import messenger

from gameplay.actions.unit.base_unit_action import BaseUnitAction
from gameplay.units.unit_base import CantMoveReason, UnitBaseClass
from managers.i18n import t_
from system.actions import Action


class WalkAction(BaseUnitAction):
    def __init__(self, instance: UnitBaseClass):
        self.unit = instance
        super().__init__(
            name=t_("actions.unit.move"),
            action=self.move_wrapper,
            condition=instance.can_move,
            on_success=self.success,
            on_failure=self.show_cant_move_popup,
            success_condition=self.is_successfull,
        )

        self.on_the_spot_action = False
        self.targeting_tile_action = True
        self.get_return_as_failure_argument = True

    def move_wrapper(self, *args, **kwargs) -> CantMoveReason:
        result = self.unit.move(*args, **kwargs)
        self._result = result
        return result

    def is_successfull(self, action: Action, *args, **kwargs) -> bool:
        if action.get_result() == CantMoveReason.COULD_MOVE:
            return True
        return False

    def success(self, *args, **kwargs):
        messenger.send("unit.action.move.success", [self.get_result()])

    def show_cant_move_popup(self, action: Action, *args, **kwargs):
        result = action.get_result()
        text, description = "", ""
        if result == CantMoveReason.NO_MOVES:
            text, description = (
                t_("ui.dialoges.unit.move_errors.no_moves.title"),
                t_("ui.dialoges.unit.move_errors.no_moves.message"),
            )
        elif result == CantMoveReason.IMPASSABLE:
            text, description = (
                t_("ui.dialoges.unit.move_errors.move_impassable.title"),
                t_("ui.dialoges.unit.move_errors.move_impassable.message"),
            )
        elif result == CantMoveReason.NO_PATH:
            text, description = (
                t_("ui.dialoges.unit.move_errors.move_path.title"),
                t_("ui.dialoges.unit.move_errors.move_path.message"),
            )
        elif result == CantMoveReason.OTHER_UNIT_ON_TILE:
            text, description = (
                t_("ui.dialoges.unit.move_errors.other_unit.title"),
                t_("ui.dialoges.unit.move_errors.other_unit.message"),
            )

        if len(text) > 0 or len(description) > 0:
            messenger.send(
                "ui.request.open.popup",
                ["unit_cant_move", text, description],
            )
        else:
            messenger.send(
                "ui.request.open.popup",
                [
                    t_("ui.dialoges.unit.move_errors.unknown_issue.message"),
                    t_("ui.dialoges.unit.move_errors.unknown_issue.message", suffix=str(result)),
                ],
            )
