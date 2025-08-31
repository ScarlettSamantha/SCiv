from typing import Any

from gameplay.messages.info import InfoMessage
from helpers.cache import Cache
from kivy.uix.image import Image
from managers.i18n import t_


class PlayerNotResearchingMessage(InfoMessage):
    key: str = "player_not_researching"
    icon: Image | None = Cache.get_icon_atlas().get_kivy_image("ui_alert.png")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            title=t_("ui.messages.research.not_active.title"),
            text=t_("ui.messages.research.not_active.message"),
            tooltip=t_("ui.messages.research.not_active.tooltip"),
            duration=InfoMessage.DURATION_PERMANENT,
            color=(1.0, 0.0, 0.0, 1.0),
            icon=self.icon,
            visible=True,
            is_closable=False,
            is_clickable=True,
            is_disabled=False,
            is_blocking=False,
            is_unique=True,
        )

    def register_on_click(self, *args: Any, **kwargs: Any) -> None:
        pass
