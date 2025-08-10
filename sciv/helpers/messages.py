from typing import TYPE_CHECKING, Any

from direct.showbase import MessengerGlobal
from managers.i18n import T_TranslationOrStr, T_TranslationOrStrOrNone
from managers.player import PlayerManager
from system.messenger import Message

if TYPE_CHECKING:
    from gameplay.player import Player


class MessageHelper:
    session_player: "Player" = PlayerManager.session_player()

    @classmethod
    def send_to_player(cls, player: "Player", message: Message, send_refresh_request: bool = True, *args: Any) -> None:
        player.messenger.add_message(message)
        if send_refresh_request:
            MessengerGlobal.messenger.send("ui.update.ui.messenger.refresh")

    @classmethod
    def send_to_all_players(cls, message: "Message", *args: Any) -> None:
        for player in PlayerManager.players().values():
            cls.send_to_player(player, message, *args)

    @classmethod
    def send_to_session_player(cls, message: "Message", *args: Any) -> None:
        cls.send_to_player(cls.session_player, message, *args)

    @classmethod
    def session_alert(
        cls,
        message: T_TranslationOrStr,
        tooltip: T_TranslationOrStrOrNone = None,
        duration: float = Message.DURATION_PERMANENT,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        from gameplay.messages.info import InfoMessage

        info_message = InfoMessage(text=message, duration=duration, tooltip=tooltip, *args, **kwargs)
        cls.send_to_session_player(info_message)
