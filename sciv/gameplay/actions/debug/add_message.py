from typing import Any

from gameplay.actions.debug.debug_action import DebugAction
from managers.i18n import Translation


class AddMessage(DebugAction):
    key = "actions.debug.add_message"
    debug_action = True

    def __init__(self):
        super().__init__(
            name=self.key,
            action=self.action_wrapper,
            condition=None,
            on_success=None,
            on_failure=None,
            success_condition=self.is_successful,
        )
        self.on_the_spot_action = True
        self.targeting_unit_action = False
        self.targeting_tile_action = False
        self.keep_targeting_after_use = True

    def action_wrapper(self, *args: Any, **kwargs: Any) -> None:
        from helpers.messages import MessageHelper

        MessageHelper.session_alert(
            message=Translation(key="ui.messages.debug.add_message.message"),
            tooltip=Translation("ui.messages.debug.add_message.tooltip"),
        )

    def is_successful(self, *args: Any, **kwargs: Any) -> bool:
        return True
