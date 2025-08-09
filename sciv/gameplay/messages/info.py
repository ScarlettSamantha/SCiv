from typing import Any, Dict, Tuple

from helpers.cache import Cache
from helpers.colors import Colors
from helpers.placeholder import Placeholder
from kivy.uix.image import Image
from managers.i18n import T_TranslationOrStr, T_TranslationOrStrOrNone
from system.messenger import Message


class InfoMessage(Message):
    def __init__(
        self,
        text: T_TranslationOrStr,
        tooltip: T_TranslationOrStrOrNone = None,
        duration: float = Message.DURATION_PERMANENT,
        color: Tuple[float, ...] = Colors.TIEL,
        icon: str | Image = "",
        visible: bool = True,
        is_closable: bool = True,
        is_clickable: bool = False,
        is_disabled: bool = False,
        is_blocking: bool = False,
        on_click_arguments: Dict[Any, Any] = {},
    ):
        super().__init__(
            text=text,
            tooltip=tooltip,
            duration=duration,
            color=color,
            icon=(Cache.get_icon_atlas().get_kivy_image("ui_alert.png") if icon == "" else icon)
            or Placeholder.getPlaceholderImagePathSmallIcon(),
            visible=visible,
            is_closable=is_closable,
            is_clickable=is_clickable,
            is_disabled=is_disabled,
            on_click_arguments=on_click_arguments,
            is_blocking=is_blocking,
        )
