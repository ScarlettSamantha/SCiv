from typing import Any, Optional, Tuple

from helpers.cache import Cache
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from menus.kivy.elements.styled import LeftAlignedLabel


class ImageLabel(BoxLayout):
    def __init__(
        self,
        img_source: str,
        text: str,
        width: Optional[int] = None,
        spacing: int = 5,
        image_size: Tuple[int, int] = (24, 24),
        keep_ratio: bool = True,
        img_y_offset: float = 0.025,
        img_x_offset: float = 0,
        font_size: Any = 16,
        text_color: Optional[Tuple[float, float, float, float]] = None,
        **kwargs: Any,
    ):
        explicit_color = kwargs.pop("color", None)
        if text_color is None and explicit_color is not None:
            text_color = explicit_color  # type: ignore

        if "orientation" not in kwargs:
            kwargs["orientation"] = "horizontal"
        if "spacing" not in kwargs:
            kwargs["spacing"] = spacing
        if "size_hint_x" not in kwargs:
            kwargs["size_hint_x"] = None

        super().__init__(**kwargs)

        self._text = text

        if width is not None:
            self.width = dp(width)  # type: ignore

        if self.size_hint_y is None:
            self.size_hint_y = None  # type: ignore

        if not getattr(self, "height", None):
            self.height = max(image_size[1], dp(30))  # type: ignore

        self.img = Cache.get_asset_archive().get_kivy_image_object(
            virtual_path=img_source,
            size_hint_x=None,
            width=image_size[0],
            size_hint_y=None,
            height=image_size[1],
            allow_stretch=True,
            keep_ratio=keep_ratio,
            pos_hint={"center_y": 0.5 + img_y_offset, "center_x": img_x_offset},
        )
        self.add_widget(self.img)

        self.label = LeftAlignedLabel(
            text=text,
            font_size=font_size,
            size_hint_x=1,
            valign="middle",
            halign="left",
            shorten=False,
            shorten_from="right",
        )

        if text_color is not None:
            self.label.color = text_color  # type: ignore

        self.add_widget(self.label)

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value
        self.label.text = value

    def set_text(self, text: str) -> None:
        self.text = text

    def set_image(self, img_source: str) -> None:
        self.img.source = img_source  # type: ignore
