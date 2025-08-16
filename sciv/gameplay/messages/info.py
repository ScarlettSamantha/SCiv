from typing import Any, Dict, Tuple

from helpers.cache import Cache
from helpers.colors import Colors
from kivy.uix.image import Image
from managers.i18n import T_TranslationOrStr, T_TranslationOrStrOrNone, t_
from system.messenger import Message


class InfoMessage(Message):
    key: str = "info_message"
    icon: Image | None = Cache.get_icon_atlas().get_kivy_image("ui_alert.png")

    def __init__(
        self,
        text: T_TranslationOrStr,
        title: T_TranslationOrStr = t_("ui.player_ui.generics.info"),
        tooltip: T_TranslationOrStrOrNone = None,
        duration: float = Message.DURATION_PERMANENT,
        color: Tuple[float, ...] = Colors.TIEL,
        icon: str | Image | None = None,
        visible: bool = True,
        is_closable: bool = True,
        is_clickable: bool = True,
        is_disabled: bool = False,
        is_blocking: bool = False,
        on_click_arguments: Dict[Any, Any] = {},
    ):
        super().__init__(
            title=title,
            text=text,
            tooltip=tooltip,
            duration=duration,
            color=color,
            visible=visible,
            is_closable=is_closable,
            is_clickable=is_clickable,
            is_disabled=is_disabled,
            on_click_arguments=on_click_arguments,
            is_blocking=is_blocking,
        )
        self._icon = (
            icon
            if isinstance(icon, Image)
            else Cache.get_icon_atlas().get_kivy_image(icon)
            if isinstance(icon, str)
            else self.icon
        )

    def get_icon(self) -> str | Image | None:
        return self._icon

    def on_click(self, *args: Any, **kwargs: Any) -> None:
        self.open(*args, **kwargs)

    def open(self, *args: Any, **kwargs: Any) -> None:
        from menus.kivy.panels.alert import AlertPanel

        icon: str | Image | None = self.get_icon()

        panel = AlertPanel(
            icon_source=icon,
            message=str(self.get_formatted_text()),
            placeholder=str(self.tooltip) if self.tooltip else "",
            submit_text=t_("ui.player_ui.generics.close"),
            on_submit=lambda text: self.hide(),
        )
        panel.open()
