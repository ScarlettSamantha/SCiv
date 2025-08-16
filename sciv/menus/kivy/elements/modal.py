from typing import Any, Callable, Dict, List, Literal, Optional

from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp, sp  # type: ignore
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView
from kivy.uix.widget import Widget
from managers.i18n import T_TranslationOrStr, t_


class OutlineButton(Button):
    outline_color: List[float] | ListProperty = ListProperty([0.0, 0.0, 0.0, 0.75])  # type: ignore
    outline_width: float | NumericProperty = NumericProperty(1)  # type: ignore
    corner_radius: float | NumericProperty = NumericProperty(6.0)  # type: ignore

    def __init__(self, **kwargs: Any):
        pad: Any | tuple[int, int] = kwargs.pop("padding", (dp(12), dp(8)))
        text_col: Any | tuple[float, float, float, Literal[1]] = kwargs.pop("color", (0.92, 0.92, 0.92, 1))

        super().__init__(**kwargs)
        self.padding = pad  # type: ignore
        self.color = text_col  # type: ignore
        self.bold = False
        self.markup = False

        self.font_size = kwargs.pop("font_size", sp(12))

        self.outline_width = 0.5  # type: ignore

        self.halign = "center"
        self.valign = "middle"
        self.bind(size=self._update_text_box)
        self._update_text_box()

        with self.canvas.after:  # type: ignore
            self._ol_color = Color(*self.outline_color)  # type: ignore
            self._ol = Line(width=dp(self.outline_width))

        self.bind(
            pos=self._update_outline,
            size=self._update_outline,
            outline_width=self._update_outline,
            outline_color=self._recolor_outline,
            corner_radius=self._update_outline,
        )

    def _update_text_box(self, *_: Any) -> None:
        px = self.padding[0] if isinstance(self.padding, (tuple, list)) else float(self.padding)  #  type: ignore
        self.text_size = (max(0.0, self.width - 2 * px), None)  # type: ignore

    def _recolor_outline(self, *_: Any) -> None:
        self._ol_color.rgba = self.outline_color  # type: ignore

    def _update_outline(self, *_: Any) -> None:
        lw = dp(float(self.outline_width))  # type: ignore
        x = self.x + lw / 2.0
        y = self.y + lw / 2.0
        w = max(0.0, self.width - lw)
        h = max(0.0, self.height - lw)
        r = max(0.0, dp(float(self.corner_radius)))  # type: ignore
        if r > 0:
            self._ol.rounded_rectangle = (x, y, w, h, r)  # type: ignore
        else:
            self._ol.rectangle = (x, y, w, h)  # type: ignore
        self._ol.width = lw  # type: ignore


class _PanelBackground(Widget):
    """Draws a black border and dark gray inner background behind content."""

    border_px: NumericProperty | int = NumericProperty(4)  #  type: ignore
    border_color: ListProperty | List[int] = ListProperty([0, 0, 0, 1])  # type: ignore
    inner_color: ListProperty | List[float] = ListProperty([0.15, 0.15, 0.15, 1])  # type: ignore

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        with self.canvas:  # type: ignore
            self._c1 = Color(*self.border_color)  # type: ignore
            self._border = Rectangle(pos=self.pos, size=self.size)  # type: ignore
            self._c2 = Color(*self.inner_color)  # type: ignore
            self._inner = Rectangle(pos=self.pos, size=self.size)  # type: ignore

        self.bind(
            pos=self._update_rects,
            size=self._update_rects,
            border_px=self._update_rects,
            border_color=self._recolor_border,
            inner_color=self._recolor_inner,
        )

    def _recolor_border(self, *_: Any) -> None:
        self._c1.rgba = self.border_color  # type: ignore

    def _recolor_inner(self, *_: Any) -> None:
        self._c2.rgba = self.inner_color  # type: ignore

    def _update_rects(self, *_: Any) -> None:
        self._border.pos = self.pos  # type: ignore
        self._border.size = self.size
        px = float(self.border_px)  # type: ignore
        self._inner.pos = (self.x + px, self.y + px)  # type: ignore
        self._inner.size = (max(0.0, self.width - 2 * px), max(0.0, self.height - 2 * px))  # type: ignore


class ModalPanel(ModalView):
    def __init__(
        self,
        close_text: T_TranslationOrStr = t_("ui.player_ui.generics.close"),
        on_close: Optional[Callable[[], None]] = None,
        border_px: int = 4,
        *args: Any,
        **kwargs: Any,
    ):
        kwargs.setdefault("size_hint", (0.6, 0.6))
        kwargs.setdefault("auto_dismiss", False)
        kwargs.pop("default_text", None)
        kwargs.pop("placeholder", None)
        kwargs.pop("submit_text", None)
        super().__init__(**kwargs)

        stack = AnchorLayout(anchor_x="center", anchor_y="center", size_hint=(1, 1))
        stack.add_widget(_PanelBackground(size_hint=(1, 1), border_px=dp(border_px)))
        self.add_widget(stack)

        content_and_actions = BoxLayout(orientation="vertical", spacing=dp(8), size_hint=(1, 1), padding=dp(border_px))
        stack.add_widget(content_and_actions)

        self.content_container = BoxLayout(orientation="vertical")
        content_and_actions.add_widget(self.content_container)

        action_bar_anchor = AnchorLayout(
            anchor_x="right",
            anchor_y="bottom",
            size_hint_y=None,
            height=dp(52),
            padding=[0, dp(8), dp(12), dp(12)],  # L, T, R, B
        )
        content_and_actions.add_widget(action_bar_anchor)

        self._buttons_box = BoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            height=dp(40),
            spacing=dp(8),
        )
        self._buttons_box.bind(minimum_width=self._on_min_width)
        action_bar_anchor.add_widget(self._buttons_box)

        self._close_btn = OutlineButton(
            text=str(close_text),
            size_hint=(None, None),
            height=dp(40),
            width=dp(120),
            background_normal="",
            background_down="",
            background_color=(0.18, 0.18, 0.18, 1),
            color=(1, 1, 1, 1),
            outline_color=(1, 1, 1, 1),
            outline_width=1,
            corner_radius=6,
        )
        self._close_btn.bind(on_release=self._do_close)
        self._buttons_box.add_widget(self._close_btn)

        self._on_close_cb = on_close

    def set_content(self, widget: Widget) -> None:
        self.content_container.clear_widgets()
        self.content_container.add_widget(widget)

    def add_action_widget(self, widget: Widget) -> None:
        self._buttons_box.add_widget(widget)

    def add_action_button(
        self,
        text: T_TranslationOrStr,
        on_press: Optional[Callable[[], None]] = None,
        width: int | float = dp(140),
        height: int | float = dp(40),
        **button_kwargs: Dict[str, Any],
    ) -> Button:
        defaults: Dict[str, Any] = dict(
            size_hint=(None, None),
            width=width,
            height=height,
            background_normal="",
            background_down="",
            background_color=(0.18, 0.18, 0.18, 1),
            color=(1, 1, 1, 1),
            outline_color=(1, 1, 1, 1),
            outline_width=1.5,
        )
        defaults.update(button_kwargs)
        btn = OutlineButton(text=str(text), **defaults)
        if on_press:
            btn.bind(on_release=lambda *_: on_press())
        self._buttons_box.add_widget(btn)
        return btn

    def _on_min_width(self, _instance: Widget, value: int):
        self._buttons_box.width = max(value, self._close_btn.width)

    def _do_close(self, *_: Any) -> None:
        self.dismiss()
        if self._on_close_cb:
            self._on_close_cb()
