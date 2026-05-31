from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional, Union

from helpers.paths import PathsHelper  # type: ignore
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp  # type: ignore
from kivy.properties import ListProperty, NumericProperty
from kivy.core.window import Window
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.widget import Widget
from managers.config import ConfigManager
from managers.i18n import T_TranslationOrStr, t_
from menus.kivy.elements.layout_debug import LayoutDebugPosition, LayoutDebugStatsBadge, denormalize_position


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

        self.font_size = kwargs.pop("font_size", dp(12))

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
        self._border.pos = self.pos
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
        width: int | float = 140,
        height: int | float = 40,
        **button_kwargs: Dict[str, Any],
    ) -> Button:
        defaults: Dict[str, Any] = dict(
            size_hint=(None, None),
            width=dp(width),
            height=dp(height),
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


class ModalImagePopup(ModalView):
    def __init__(
        self,
        *,
        image: Optional[Union[str, "Image"]] = None,
        title: str = "",
        description: str = "",
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("auto_dismiss", False)
        kwargs.setdefault("size_hint", (0.8, 0.8))
        kwargs.setdefault("pos_hint", {"center_x": 0.5, "center_y": 0.5})
        layout_debug_id = str(kwargs.pop("layout_debug_id", "popup.modal_image"))

        image_source = kwargs.pop("image_source", None)
        if image_source is not None and image is None:
            image = image_source

        message: str = kwargs.pop("message", "")
        if message and not description:
            description = message

        super().__init__(**kwargs)

        self._layout_debug_config: ConfigManager = ConfigManager.get_singleton_instance()
        self._layout_debug_item_id: str = layout_debug_id
        self._layout_debug_dragging: bool = False
        self._layout_debug_drag_offset: tuple[float, float] = (0.0, 0.0)
        self._layout_debug_position_initialized: bool = False

        root = FloatLayout(size_hint=(1, 1))
        self._root_layout = root
        self.add_widget(root)

        self._bg_img = Image(
            size_hint=(None, None),
            allow_stretch=False,
            keep_ratio=True,
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        root.add_widget(self._bg_img)

        self._overlay = BoxLayout(
            orientation="vertical",
            size_hint=(0.85, None),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            spacing=dp(8),
            padding=(dp(16), dp(16), dp(16), dp(16)),
        )
        root.add_widget(self._overlay)

        with self._overlay.canvas.before:
            Color(0, 0, 0, 0.70)
            self._overlay_bg = Rectangle(pos=self._overlay.pos, size=self._overlay.size)  # type: ignore

        self._title_lbl = Label(
            text=f"[b]{title}[/b]" if title else "",
            markup=True,
            halign="center",
            valign="middle",
            size_hint=(1, None),
        )
        self._overlay.add_widget(self._title_lbl)

        self._desc_lbl = Label(
            text=description or "",
            markup=True,
            halign="center",
            valign="middle",
            size_hint=(1, None),
        )
        self._overlay.add_widget(self._desc_lbl)

        close_text = str(t_("ui.player_ui.generics.close"))

        self._btn_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(44),
            padding=(0, dp(4), 0, 0),
        )
        self._overlay.add_widget(self._btn_row)

        self._close_btn = Button(
            text=close_text,
            size_hint=(None, None),
            width=dp(120),
            height=dp(36),
            halign="center",
            valign="middle",
            background_normal="",
            background_color=(0, 0, 0, 0.95),
            color=(0.92, 0.92, 0.92, 1.0),
        )
        self._close_btn.bind(on_release=lambda *_: self.dismiss())
        self._btn_row.add_widget(BoxLayout(size_hint=(1, 1)))
        self._btn_row.add_widget(self._close_btn)
        self._btn_row.add_widget(BoxLayout(size_hint=(1, 1)))

        self._layout_debug_badge = LayoutDebugStatsBadge()
        root.add_widget(self._layout_debug_badge)
        self._layout_debug_badge.hide()

        self.bind(size=self._center_image, pos=self._center_image)
        self._bg_img.bind(texture=self._center_image)
        self._overlay.bind(pos=self._on_overlay_resize_move, size=self._on_overlay_resize_move)

        self._recompute_overlay_height()
        self.bind(size=lambda *_: self._recompute_overlay_height())

        self.set_content(image=image, title=title, description=description)

    def _layout_debug_drag_enabled(self) -> bool:
        return self._layout_debug_config.get_debug_mode() and self._layout_debug_config.get_ui_layout_drag_enabled()

    def _layout_debug_window_size(self) -> tuple[float, float]:
        if Window is not None:
            return (float(Window.width), float(Window.height))
        return (max(float(self.width), 1.0), max(float(self.height), 1.0))

    def _layout_debug_saved_position(self) -> LayoutDebugPosition | None:
        data = self._layout_debug_config.get_ui_layout_position(self._layout_debug_item_id)
        if data is None:
            return None
        return LayoutDebugPosition(x=float(data.get("x", 0.0)), y=float(data.get("y", 0.0)))

    def _layout_debug_clamp_position(self, pos_x: float, pos_y: float) -> tuple[float, float]:
        window_width, window_height = self._layout_debug_window_size()
        return (
            max(0.0, min(pos_x, window_width - float(self.width))),
            max(0.0, min(pos_y, window_height - float(self.height))),
        )

    def _layout_debug_apply_initial_position(self) -> None:
        if self._layout_debug_position_initialized:
            return

        self.pos_hint = {}
        saved_position = self._layout_debug_saved_position()
        if saved_position is not None:
            self.pos = self._layout_debug_clamp_position(*denormalize_position(saved_position, self._layout_debug_window_size()))
        else:
            window_width, window_height = self._layout_debug_window_size()
            self.pos = self._layout_debug_clamp_position(
                (window_width - float(self.width)) / 2.0,
                (window_height - float(self.height)) / 2.0,
            )

        self._layout_debug_position_initialized = True
        self._layout_debug_update_badge()

    def _layout_debug_store_position(self) -> None:
        window_width, window_height = self._layout_debug_window_size()
        self._layout_debug_config.set_ui_layout_position(
            self._layout_debug_item_id,
            float(self.x) / max(window_width, 1.0),
            float(self.y) / max(window_height, 1.0),
        )

    def _layout_debug_update_badge(self) -> None:
        self._layout_debug_badge.pos = (
            max(float(dp(8)), float(self.width) - float(self._layout_debug_badge.width) - float(dp(8))),
            max(float(dp(8)), float(self.height) - float(self._layout_debug_badge.height) - float(dp(8))),
        )

        if self._layout_debug_dragging:
            self._layout_debug_badge.show_metrics(
                self._layout_debug_item_id,
                pos_x=float(self.x),
                pos_y=float(self.y),
                width=float(self.width),
                height=float(self.height),
            )
        else:
            self._layout_debug_badge.hide()

    def _layout_debug_touch_in_handle(self, touch_pos: tuple[float, float]) -> bool:
        return touch_pos[1] >= float(self.top) - float(dp(40))

    def on_open(self, *args: Any) -> None:
        super().on_open(*args)
        self._layout_debug_apply_initial_position()

    def on_touch_down(self, touch: Any) -> bool:
        if self._layout_debug_drag_enabled() and self.collide_point(*touch.pos) and self._layout_debug_touch_in_handle(touch.pos):
            touch.grab(self)
            self._layout_debug_dragging = True
            self._layout_debug_drag_offset = (float(touch.x - self.x), float(touch.y - self.y))
            self._layout_debug_update_badge()
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch: Any) -> bool:
        if touch.grab_current is self:
            self.pos = self._layout_debug_clamp_position(
                float(touch.x) - self._layout_debug_drag_offset[0],
                float(touch.y) - self._layout_debug_drag_offset[1],
            )
            self._layout_debug_update_badge()
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch: Any) -> bool:
        if touch.grab_current is self:
            touch.ungrab(self)
            self._layout_debug_dragging = False
            self._layout_debug_store_position()
            self._layout_debug_update_badge()
            return True
        return super().on_touch_up(touch)

    def set_content(
        self,
        *,
        image: Optional[Union[str, "Image"]] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        if image is not None:
            self._apply_image(img=image)

        if title is not None:
            self._title_lbl.text = f"[b]{title}[/b]" if title else ""

        if description is not None:
            self._desc_lbl.text = description or ""

        self._recompute_overlay_height()
        self._center_image()

    def _apply_image(self, img: Union[str, "Image"]) -> None:
        if isinstance(img, Image):
            if getattr(img, "texture", None) is not None:
                self._bg_img.texture = img.texture
                self._bg_img.source = ""
            else:
                self._bg_img.source = img.source
            return

        path: Path = PathsHelper.get_base_path() / img
        self._bg_img.source = str(path)

    def _center_image(self, *_: Any) -> None:
        tex = self._bg_img.texture
        if not tex:
            return

        iw, ih = tex.size
        bw, bh = self.width, self.height  # type: ignore
        if iw <= 0 or ih <= 0 or bw <= 0 or bh <= 0:
            return

        scale = min(bw / iw, bh / ih)  # type: ignore
        w, h = iw * scale, ih * scale  # type: ignore

        self._bg_img.size = (w, h)
        self._bg_img.pos = (self.center_x - w / 2.0, self.center_y - h / 2.0)  # type: ignore

    def _recompute_overlay_height(self) -> None:
        pad_l, pad_t, pad_r, pad_b = (  #  type: ignore
            self._overlay.padding  # type: ignore
            if isinstance(self._overlay.padding, (tuple, list))  # type: ignore
            else (dp(16), dp(16), dp(16), dp(16))
        )
        spacing = self._overlay.spacing or 0
        total = pad_t + pad_b + spacing * (len(self._overlay.children) - 1)  # type: ignore
        for child in self._overlay.children:
            total += getattr(child, "height", dp(0))  # type: ignore
        min_h = dp(120)
        max_h = self.height * 0.75  # type: ignore
        self._overlay.height = max(min_h, min(total, max_h))  # type: ignore

    def _on_overlay_resize_move(self, *_: Any) -> None:
        if hasattr(self, "_overlay_bg"):
            self._overlay_bg.pos = self._overlay.pos  # type: ignore
            self._overlay_bg.size = self._overlay.size  # type: ignore
