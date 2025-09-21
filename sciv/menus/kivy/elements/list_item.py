from typing import Any

from helpers.colors import Tuple4f
from menus.kivy.elements.button_value import ButtonValue


class ListItem(ButtonValue):
    def __init__(
        self,
        text: str = "",
        text_prefix: str = "",
        text_suffix: str = "",
        background_color: Tuple4f = (1, 1, 1, 0.3),
        halign: str = "left",
        valign: str = "bottom",
        markup: bool = True,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(text=f"{text_prefix}{text}{text_suffix}", *args, **kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = background_color
        self.halign = halign
        self.valign = valign
        self.padding_x = 10
        self.padding_y = 5
        self.markup = markup
