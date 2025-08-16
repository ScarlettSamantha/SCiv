from gameplay.condition import Conditions, IsPlayerNotResearchingCondition
from gameplay.messages.player_not_researching import PlayerNotResearchingMessage
from gameplay.notification import PersistentNotification
from helpers.messages import MessageHelper


class IsNotResearching(PersistentNotification):
    key: str = "IS_RESEARCHING"
    conditions: Conditions = Conditions([IsPlayerNotResearchingCondition()])
    persistent: bool = True
    message: PlayerNotResearchingMessage = PlayerNotResearchingMessage()

    def __init__(self):
        super().__init__()
        self.message_active = False

    def on_trigger(self) -> None:
        from helpers.messages import MessageHelper

        if self.message_active:
            return

        MessageHelper.send_to_session_player(self.message)

        self.message_active = True

    def on_dismiss(self) -> None:
        MessageHelper.remove_message_from_session_player(self.message)
        self.message_active = False
