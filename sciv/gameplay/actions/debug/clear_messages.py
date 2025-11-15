from typing import Any

from direct.showbase import MessengerGlobal
from gameplay.actions.debug.debug_action import DebugAction


class ClearMessages(DebugAction):
    key = "actions.debug.clear_messages"
    debug_action = True
    category = "Messages"

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

        MessageHelper.remove_all_messages_from_session_player()
        MessengerGlobal.messenger.send("ui.update.ui.messenger.refresh")

    def is_successful(self, *args: Any, **kwargs: Any) -> bool:
        return True
