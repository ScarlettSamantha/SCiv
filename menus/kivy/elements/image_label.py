from typing import Optional, Tuple

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label


class ImageLabel(BoxLayout):
    def __init__(
        self,
        img_source,
        text,
        width: Optional[int] = None,
        spacing: int = 5,
        image_size: Tuple[int, int] = (24, 24),
        keep_ratio: bool = True,
        img_y_offset: float = 0.025,
        font_size: int = 12,
        **kwargs,
    ):
        super().__init__(orientation="horizontal", spacing=spacing, size_hint_x=None, **kwargs)

        # Image (adjust y-position with pos_hint)
        self.img = Image(
            source=img_source,
            size_hint=(None, None),
            size=image_size,
            allow_stretch=True,
            keep_ratio=keep_ratio,
            pos_hint={"center_y": 0.5 + img_y_offset},  # Move image up slightly,
            width=image_size[0],
        )
        self.add_widget(self.img)

        # Label
        self.label = Label(text=text, font_size=font_size, size_hint_x=1, valign="middle", halign="left")
        self.label.bind(texture_size=self.label.setter("size"))  # type: ignore # Ensure proper text alignment
        self.add_widget(self.label)

    def set_text(self, text: str):
        self.label.text = text

    def set_image(self, img_source: str):
        self.img.source = img_source
