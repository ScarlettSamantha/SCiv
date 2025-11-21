from typing import Any

from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from menus.kivy.theme import CIV_THEME, ButtonStyle, LabelStyle, PanelStyle, TextInputStyle


def _resolve_font_size(value: Any, default: float = 14.0) -> float:
    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        s = value.strip().lower()

        if s.endswith("dp") or s.endswith("sp"):
            try:
                return float(dp(float(s[:-2])))
            except ValueError:
                return float(dp(default))

        try:
            return float(s)
        except ValueError:
            return float(dp(default))

    return float(dp(default))


class Panel(BoxLayout):
    def __init__(self, style: PanelStyle | None = None, **kwargs: Any) -> None:
        style_value = style or CIV_THEME.panel

        if "padding" not in kwargs:
            left, top, right, bottom = style_value.padding
            kwargs["padding"] = (
                dp(left),
                dp(top),
                dp(right),
                dp(bottom),
            )

        if "spacing" not in kwargs:
            kwargs["spacing"] = dp(style_value.spacing)

        super().__init__(**kwargs)
        self._bg_rect: Rectangle

        with self.canvas.before:  # type: ignore
            Color(*style_value.background)
            self._bg_rect = Rectangle(size=self.size, pos=self.pos)  # type: ignore

        self.bind(size=self._update_rect, pos=self._update_rect)  # type: ignore

    def _update_rect(self, instance: Widget, _value: Any) -> None:
        self._bg_rect.size = instance.size  # type: ignore
        self._bg_rect.pos = instance.pos  # type: ignore


class DarkPanel(Panel):
    def __init__(self, **kwargs: Any) -> None:
        alt_style = PanelStyle(
            padding=CIV_THEME.panel.padding,
            spacing=CIV_THEME.panel.spacing,
            background=CIV_THEME.palette.background_panel_alt,
        )
        super().__init__(alt_style, **kwargs)


def _apply_label_style(widget: Label, style: LabelStyle) -> None:  # type: ignore
    widget.color = style.color  # type: ignore
    widget.font_size = _resolve_font_size(style.font_size)  # type: ignore
    widget.markup = style.markup
    widget.halign = style.halign
    widget.valign = style.valign  # type: ignore
    widget.bold = style.bold  # type: ignore


class ThemedLabel(Label):
    def __init__(self, style_key: str, **kwargs: Any) -> None:
        style = CIV_THEME.labels[style_key]

        font_size_spec = kwargs.pop("font_size", style.font_size)
        color = kwargs.pop("color", style.color)
        markup = kwargs.pop("markup", style.markup)
        halign = kwargs.pop("halign", style.halign)
        valign = kwargs.pop("valign", style.valign)

        super().__init__(**kwargs)

        self.color = color  # type: ignore
        self.markup = markup
        self.halign = halign
        self.valign = valign  # type: ignore
        self.bold = style.bold  # type: ignore
        self.font_size = _resolve_font_size(font_size_spec)  # type: ignore

        self.bind(size=self._update_text_size)  # type: ignore

    def _update_text_size(self, instance: Label, _value: Any) -> None:
        instance.text_size = instance.size  # type: ignore


class TitleLabel(ThemedLabel):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__("title", **kwargs)


class SubtitleLabel(ThemedLabel):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__("subtitle", **kwargs)


class SectionLabel(ThemedLabel):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__("section", **kwargs)


class LeftAlignedLabel(ThemedLabel):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__("body", **kwargs)


class MutedLabel(ThemedLabel):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__("body_muted", **kwargs)


def _apply_button_style(widget: Button, style: ButtonStyle) -> None:
    widget.background_normal = ""  # type: ignore
    widget.background_down = ""  # type: ignore
    widget.color = style.text  # type: ignore
    widget.font_size = _resolve_font_size(style.font_size)  # type: ignore
    widget.bold = style.bold  # type: ignore


class ThemedButton(Button):
    def __init__(self, style_key: str, **kwargs: Any) -> None:
        style = CIV_THEME.buttons[style_key]

        if "size_hint" not in kwargs and style.width is not None:
            kwargs["size_hint"] = (None, None)

        if "height" not in kwargs:
            kwargs["height"] = dp(style.height)

        if style.width is not None and "width" not in kwargs:
            kwargs["width"] = dp(style.width)

        super().__init__(**kwargs)
        self._style: ButtonStyle = style
        _apply_button_style(self, style)
        self._refresh_background()
        self.bind(state=self._on_state_change, disabled=self._on_disabled_change)  # type: ignore

    def _refresh_background(self) -> None:
        if self.disabled:  # type: ignore
            self.background_color = self._style.background_disabled  # type: ignore
        else:
            if self.state == "down":  # type: ignore
                self.background_color = self._style.background_hover  # type: ignore
            else:
                self.background_color = self._style.background  # type: ignore

    def _on_state_change(self, _instance: Button, _value: str) -> None:
        self._refresh_background()

    def _on_disabled_change(self, _instance: Button, _value: bool) -> None:
        self._refresh_background()


class PrimaryButton(ThemedButton):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__("primary", **kwargs)


class SecondaryButton(ThemedButton):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__("secondary", **kwargs)


class DangerButton(ThemedButton):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__("danger", **kwargs)


class IconButton(ThemedButton):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__("icon", **kwargs)


class MenuCheckbox(CheckBox):
    def __init__(self, **kwargs: Any) -> None:
        style = CIV_THEME.checkbox

        if "size_hint" not in kwargs:
            kwargs["size_hint"] = (None, None)

        if "size" not in kwargs:
            kwargs["size"] = (dp(style.size[0]), dp(style.size[1]))

        super().__init__(**kwargs)  # type: ignore
        self._style = style
        self._update_color_from_state(self.active)  # type: ignore
        self.bind(active=self._on_active_change)  # type: ignore

    def _update_color_from_state(self, active: bool) -> None:
        if active:
            self.color = self._style.color_active  # type: ignore
        else:
            self.color = self._style.color_inactive  # type: ignore

    def _on_active_change(self, _instance: CheckBox, value: bool) -> None:
        self._update_color_from_state(value)


class InputField(TextInput):
    def __init__(self, **kwargs: Any) -> None:
        style: TextInputStyle = CIV_THEME.text_input

        font_size_spec = kwargs.pop("font_size", style.font_size)

        if "foreground_color" not in kwargs:
            kwargs["foreground_color"] = style.foreground

        if "background_color" not in kwargs:
            kwargs["background_color"] = style.background

        if "cursor_color" not in kwargs:
            kwargs["cursor_color"] = style.cursor

        if "padding" not in kwargs:
            kwargs["padding"] = [
                dp(style.padding_x),
                dp(style.padding_y),
                dp(style.padding_x),
                dp(style.padding_y),
            ]

        if "size_hint_y" not in kwargs:
            kwargs["size_hint_y"] = None

        if "height" not in kwargs:
            kwargs["height"] = dp(40)

        super().__init__(**kwargs)  # type: ignore

        self.font_size = _resolve_font_size(font_size_spec)  # type: ignore
        self.hint_text_color = style.placeholder  # type: ignore


class ThemedSlider(Slider):
    def __init__(self, **kwargs: Any) -> None:
        style = CIV_THEME.slider

        if "size_hint_y" not in kwargs:
            kwargs["size_hint_y"] = None

        if "height" not in kwargs:
            kwargs["height"] = dp(style.height)

        if "cursor_size" not in kwargs:
            kwargs["cursor_size"] = (dp(18), dp(style.height))

        if "cursor_color" not in kwargs:
            kwargs["cursor_color"] = CIV_THEME.palette.accent_primary

        if "background_width" not in kwargs:
            kwargs["background_width"] = dp(2)

        if "value_track" not in kwargs:
            kwargs["value_track"] = True

        if "value_track_color" not in kwargs:
            kwargs["value_track_color"] = CIV_THEME.palette.accent_primary

        super().__init__(**kwargs)


class ThemedSpinner(Spinner):
    def __init__(self, **kwargs: Any) -> None:
        style = CIV_THEME.buttons["secondary"]

        if "size_hint" not in kwargs:
            kwargs["size_hint"] = (None, None)

        if "height" not in kwargs:
            kwargs["height"] = dp(style.height)

        if "width" not in kwargs:
            if style.width is not None:
                kwargs["width"] = dp(style.width)
            else:
                kwargs["width"] = dp(200.0)

        font_size_spec = kwargs.pop("font_size", style.font_size)

        if "background_normal" not in kwargs:
            kwargs["background_normal"] = ""

        if "background_down" not in kwargs:
            kwargs["background_down"] = ""

        if "background_color" not in kwargs:
            kwargs["background_color"] = style.background

        if "color" not in kwargs:
            kwargs["color"] = style.text

        super().__init__(**kwargs)  # type: ignore
        self.font_size = _resolve_font_size(font_size_spec)  # type: ignore
        self.disabled_color = CIV_THEME.palette.text_muted  # type: ignore
