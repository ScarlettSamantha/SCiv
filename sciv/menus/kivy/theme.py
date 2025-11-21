from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from helpers.colors import Colors

ColorRGBA = Tuple[float, float, float, float]


@dataclass(frozen=True)
class ColorPalette:
    background: ColorRGBA
    background_panel: ColorRGBA
    background_panel_alt: ColorRGBA
    accent_primary: ColorRGBA
    accent_primary_soft: ColorRGBA
    accent_gold: ColorRGBA
    accent_danger: ColorRGBA
    text: ColorRGBA
    text_subtle: ColorRGBA
    text_muted: ColorRGBA
    border: ColorRGBA
    border_soft: ColorRGBA


@dataclass(frozen=True)
class ButtonStyle:
    background: ColorRGBA
    background_hover: ColorRGBA
    background_disabled: ColorRGBA
    text: ColorRGBA
    font_size: str
    height: float
    width: Optional[float]
    bold: bool


@dataclass(frozen=True)
class LabelStyle:
    color: ColorRGBA
    font_size: str
    markup: bool
    halign: str
    valign: str
    bold: bool


@dataclass(frozen=True)
class CheckboxStyle:
    size: Tuple[float, float]
    color_active: ColorRGBA
    color_inactive: ColorRGBA


@dataclass(frozen=True)
class PanelStyle:
    padding: Tuple[float, float, float, float]
    spacing: float
    background: ColorRGBA


@dataclass(frozen=True)
class TextInputStyle:
    background: ColorRGBA
    foreground: ColorRGBA
    placeholder: ColorRGBA
    cursor: ColorRGBA
    font_size: str
    padding_x: float
    padding_y: float


@dataclass(frozen=True)
class SliderStyle:
    height: float


@dataclass(frozen=True)
class UiTheme:
    palette: ColorPalette
    buttons: Dict[str, ButtonStyle]
    labels: Dict[str, LabelStyle]
    checkbox: CheckboxStyle
    panel: PanelStyle
    text_input: TextInputStyle
    slider: SliderStyle


_palette = ColorPalette(
    background=Colors.UI_BACKGROUND,
    background_panel=Colors.UI_BACKGROUND_PANEL,
    background_panel_alt=Colors.UI_BACKGROUND_PANEL_ALT,
    accent_primary=Colors.UI_ACCENT_PRIMARY,
    accent_primary_soft=Colors.UI_ACCENT_PRIMARY_SOFT,
    accent_gold=Colors.UI_ACCENT_SECONDARY,
    accent_danger=Colors.UI_ACCENT_DANGER,
    text=Colors.UI_TEXT,
    text_subtle=Colors.UI_TEXT_SUBTLE,
    text_muted=Colors.UI_TEXT_MUTED,
    border=Colors.UI_BORDER,
    border_soft=Colors.UI_BORDER_SOFT,
)

_button_primary = ButtonStyle(
    background=_palette.accent_primary,
    background_hover=_palette.accent_gold,
    background_disabled=Colors.UI_BUTTON_PRIMARY_DISABLED,
    text=_palette.text,
    font_size="18sp",
    height=48.0,
    width=200.0,
    bold=True,
)

_button_secondary = ButtonStyle(
    background=Colors.UI_BUTTON_SECONDARY,
    background_hover=_palette.accent_primary_soft,
    background_disabled=Colors.UI_BUTTON_SECONDARY_DISABLED,
    text=_palette.text,
    font_size="16sp",
    height=40.0,
    width=None,
    bold=False,
)

_button_danger = ButtonStyle(
    background=_palette.accent_danger,
    background_hover=Colors.UI_ACCENT_DANGER_HOVER,
    background_disabled=Colors.UI_BUTTON_DANGER_DISABLED,
    text=_palette.text,
    font_size="16sp",
    height=40.0,
    width=None,
    bold=False,
)

_button_icon = ButtonStyle(
    background=_palette.background_panel_alt,
    background_hover=_palette.accent_primary_soft,
    background_disabled=Colors.UI_BUTTON_ICON_DISABLED,
    text=_palette.text,
    font_size="20sp",
    height=40.0,
    width=40.0,
    bold=False,
)

_label_title = LabelStyle(
    color=_palette.text,
    font_size="32sp",
    markup=True,
    halign="left",
    valign="middle",
    bold=True,
)

_label_subtitle = LabelStyle(
    color=_palette.text_subtle,
    font_size="16sp",
    markup=False,
    halign="left",
    valign="middle",
    bold=False,
)

_label_section = LabelStyle(
    color=_palette.text,
    font_size="18sp",
    markup=True,
    halign="left",
    valign="middle",
    bold=True,
)

_label_body = LabelStyle(
    color=_palette.text,
    font_size="16sp",
    markup=False,
    halign="left",
    valign="middle",
    bold=False,
)

_label_body_muted = LabelStyle(
    color=_palette.text_muted,
    font_size="14sp",
    markup=False,
    halign="left",
    valign="middle",
    bold=False,
)

_checkbox_style = CheckboxStyle(
    size=(28.0, 28.0),
    color_active=_palette.accent_primary,
    color_inactive=_palette.text_muted,
)

_panel_style = PanelStyle(
    padding=(32.0, 24.0, 32.0, 24.0),
    spacing=16.0,
    background=_palette.background_panel,
)

_text_input_style = TextInputStyle(
    background=Colors.UI_INPUT_BACKGROUND,
    foreground=_palette.text,
    placeholder=_palette.text_muted,
    cursor=_palette.accent_primary,
    font_size="16sp",
    padding_x=12.0,
    padding_y=10.0,
)

_slider_style = SliderStyle(
    height=28.0,
)

CIV_THEME = UiTheme(
    palette=_palette,
    buttons={
        "primary": _button_primary,
        "secondary": _button_secondary,
        "danger": _button_danger,
        "icon": _button_icon,
    },
    labels={
        "title": _label_title,
        "subtitle": _label_subtitle,
        "section": _label_section,
        "body": _label_body,
        "body_muted": _label_body_muted,
    },
    checkbox=_checkbox_style,
    panel=_panel_style,
    text_input=_text_input_style,
    slider=_slider_style,
)
