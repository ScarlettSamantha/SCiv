from direct.showbase.MessengerGlobal import messenger

from gameplay.units.unit_base import CantMoveReason, UnitBaseClass
from managers.i18n import t_
from system.actions import Action


class WalkAction(Action):
    def __init__(self, instance: UnitBaseClass):
        super().__init__(
            name=t_("actions.unit.move"),
            action=instance.move,
            condition=instance.can_move,
            on_failure=self.show_cant_move_popup,
        )
        self.on_the_spot_action = False
        self.targeting_tile_action = True
        self.get_return_as_failure_argument = True

    def show_cant_move_popup(self, action: Action, reason: CantMoveReason, *args, **kwargs):
        result = action.get_result()
        text, description = "", ""
        if result == CantMoveReason.NO_MOVES:
            text, description = (
                t_("ui.dialoges.unit_cant_move_no_moves.message"),
                t_("ui.dialoges.unit_cant_move_no_moves.description"),
            )

        elif result == CantMoveReason.IMPASSABLE:
            text, description = (
                t_("ui.dialoges.unit_cant_move_impassable.title"),
                t_("ui.dialoges.unit_cant_move_impassable.message"),
            )
        elif result == CantMoveReason.NO_PATH:
            text, description = (
                t_("ui.dialoges.unit_cant_move_path.title"),
                t_("ui.dialoges.unit_cant_move_path.message"),
            )

        if len(text) > 0 or len(description) > 0:
            messenger.send(
                "ui.request.open.popup",
                ["unit_cant_move", text, description],
            )
