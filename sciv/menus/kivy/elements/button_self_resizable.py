from typing import Any, Tuple

from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget


class SelfResizableButton(ButtonBehavior, BoxLayout):
    text = StringProperty("")
    image_source = StringProperty("")
    markup = BooleanProperty(False)

    def __init__(self, **kwargs: Any):
        if "background_color" in kwargs:
            kwargs.pop("background_color")  # type: ignore
        super().__init__(orientation="horizontal", spacing=6, padding=4, **kwargs)  # type: ignore

        self.image_widget = Image(size_hint=(None, 1), opacity=0, width=0)
        self.label_widget = Label(text=self.text, markup=self.markup, halign="left", valign="middle", size_hint=(1, 1))

        self.add_widget(self.image_widget)
        self.add_widget(self.label_widget)

        self.bind(text=self._update_text)
        self.bind(image_source=self._update_image)
        self.bind(markup=self._update_markup)
        self.label_widget.bind(texture_size=self._update_size)  # type: ignore
        self.image_widget.bind(texture_size=self._update_image_size)  # type: ignore

        self._update_text(self, self.text)
        self._update_image(self, self.image_source)
        self._update_markup(self, self.markup)

    def _update_text(self, instance: Widget, value: str) -> None:
        self.label_widget.text = value

    def _update_markup(self, instance: Widget, value: bool) -> None:
        self.label_widget.markup = value

    def _update_image(self, instance: Widget, value: str) -> None:
        if value:
            self.image_widget.source = value
            self.image_widget.opacity = 1
        else:
            self.image_widget.source = ""
            self.image_widget.opacity = 0
            self.image_widget.width = 0
        self._update_size()

    def _update_image_size(self, instance: Widget, texture_size: Tuple[int, int]) -> None:
        if not texture_size or texture_size == (0, 0):
            self.image_widget.width = 0
            return

        aspect_ratio = texture_size[0] / texture_size[1]
        button_height = self.label_widget.texture_size[1]  # type: ignore
        max_image_height = button_height  # type: ignore
        self.image_widget.width = max_image_height * aspect_ratio

        self._update_size()

    def _update_size(self, *args: Any) -> None:
        padding_x, padding_y = 20, 10
        label_width = self.label_widget.texture_size[0]  # type: ignore
        image_width = self.image_widget.width if self.image_widget.opacity > 0 else 0  # type: ignore

        self.width = label_width + image_width + self.spacing + padding_x  # type: ignore
        self.height = (
            max(
                self.label_widget.texture_size[1],  # type: ignore
                self.image_widget.texture_size[1] if self.image_widget.opacity > 0 else 0,  # type: ignore
            )
            + padding_y
        )
