from typing import Any

from kivy.graphics import Color, Rectangle  # type: ignore
from kivy.metrics import dp  # type: ignore
from kivy.uix.boxlayout import BoxLayout  # type: ignore
from kivy.uix.button import Button  # type: ignore
from kivy.uix.checkbox import CheckBox  # type: ignore
from kivy.uix.label import Label  # type: ignore
from kivy.uix.widget import Widget  # type: ignore


class DarkPanel(BoxLayout):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        with self.canvas.before:  # type: ignore
            Color(0.08, 0.08, 0.12, 0.9)
            self._bg_rect = Rectangle(size=self.size, pos=self.pos)  # type: ignore
        self.bind(size=self._update_rect, pos=self._update_rect)  # type: ignore

    def _update_rect(self, instance: Widget, _value: Any) -> None:
        self._bg_rect.size = instance.size  # type: ignore
        self._bg_rect.pos = instance.pos  # type: ignore


class LeftAlignedLabel(Label):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("halign", "left")
        kwargs.setdefault("valign", "middle")
        super().__init__(**kwargs)
        self.bind(size=self._update_text_size)  # type: ignore

    def _update_text_size(self, instance: Label, _value: Any) -> None:
        instance.text_size = instance.size  # type: ignore


class TitleLabel(LeftAlignedLabel):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("font_size", "32sp")
        kwargs.setdefault("markup", True)
        super().__init__(**kwargs)


class SubtitleLabel(LeftAlignedLabel):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("font_size", "16sp")
        kwargs.setdefault("color", (0.75, 0.75, 0.8, 1.0))
        super().__init__(**kwargs)


class SectionLabel(LeftAlignedLabel):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("font_size", "16sp")
        super().__init__(**kwargs)


class PrimaryButton(Button):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("height", dp(48))
        kwargs.setdefault("width", dp(200))
        kwargs.setdefault("font_size", "18sp")
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", (0.18, 0.2, 0.26, 1.0))
        kwargs.setdefault("color", (1.0, 1.0, 1.0, 1.0))
        super().__init__(**kwargs)
        self.disabled_color = (0.7, 0.7, 0.7, 0.6)  # type: ignore


class SecondaryButton(Button):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("height", dp(40))
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", (0.18, 0.2, 0.26, 1.0))
        kwargs.setdefault("color", (1.0, 1.0, 1.0, 1.0))
        super().__init__(**kwargs)


class DangerButton(Button):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("size_hint", (0.15, 1.0))
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", (0.32, 0.18, 0.18, 1.0))
        kwargs.setdefault("color", (1.0, 0.8, 0.8, 1.0))
        kwargs.setdefault("font_size", "16sp")
        super().__init__(**kwargs)


class IconButton(Button):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("width", dp(40))
        kwargs.setdefault("height", dp(40))
        kwargs.setdefault("font_size", "20sp")
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", (0.32, 0.24, 0.12, 1.0))
        kwargs.setdefault("color", (1.0, 1.0, 1.0, 1.0))
        super().__init__(**kwargs)


class MenuCheckbox(CheckBox):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(28), dp(28)))
        super().__init__(**kwargs)  # type: ignore
