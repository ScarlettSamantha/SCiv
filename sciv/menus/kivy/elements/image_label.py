from typing import Any, Optional, Tuple

from kivy.metrics import dp  # type: ignore
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from helpers.cache import Cache
from helpers.windows import WindowsHelper


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
        font_size: int = 16,
        text_color: Tuple[float, float, float, float] = (1, 1, 1, 1),
        **kwargs: Any,
    ):
        super().__init__(orientation="horizontal", spacing=spacing, size_hint_x=None, **kwargs)

        self._text = text  # internal storage
        self.width = width if width else dp(550)
        self.size_hint_y = None
        self.height = max(image_size[1], dp(30))

        path = str(Cache.get_icon_atlas().get_real_path_for_virtual_path(img_source))

        if not path:
            raise ValueError(f"Image source '{img_source}' not found in icon atlas.")

        if WindowsHelper.is_windows():
            # Convert to Unix path if not on Windows
            path = WindowsHelper.unix_to_win32_path(path)

        # Image with fixed width
        self.img = Image(
            source=path,
            size_hint_x=None,
            width=image_size[0],
            size_hint_y=None,
            height=image_size[1],
            allow_stretch=True,
            keep_ratio=keep_ratio,
            pos_hint={"center_y": 0.5 + img_y_offset, "center_x": img_x_offset},
        )
        self.add_widget(self.img)

        # Label fills rest
        self.label = Label(
            text=text,
            font_size=font_size,
            size_hint_x=1,  # TAKE REMAINING SPACE
            valign="middle",
            halign="left",
            color=text_color,
            shorten=False,
            shorten_from="right",
        )
        self.label.bind(size=self._update_text_size)  # type: ignore
        self.add_widget(self.label)

    def _update_text_size(self, instance: Widget, value: Tuple[float, float]):
        instance.text_size = (instance.width, None)  # type: ignore

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str):
        self._text = value
        self.label.text = value

    def set_text(self, text: str):
        self.text = text  # Redirect to property

    def set_image(self, img_source: str):
        self.img.source = img_source
