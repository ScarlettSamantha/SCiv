from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

if TYPE_CHECKING:
    from game import OpenCiv


type PositionChangedCallback = Callable[[str, tuple[float, float]], None]


@dataclass(slots=True)
class LayoutDebugPosition:
    x: float
    y: float


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def normalize_position(position: tuple[float, float], window_size: tuple[float, float]) -> LayoutDebugPosition:
    window_width, window_height = window_size
    safe_width = max(window_width, 1.0)
    safe_height = max(window_height, 1.0)
    return LayoutDebugPosition(x=position[0] / safe_width, y=position[1] / safe_height)


def denormalize_position(position: LayoutDebugPosition, window_size: tuple[float, float]) -> tuple[float, float]:
    window_width, window_height = window_size
    return (position.x * window_width, position.y * window_height)


def format_layout_debug_metrics(
    item_id: str,
    *,
    pos_x: float,
    pos_y: float,
    width: float,
    height: float,
) -> str:
    return (
        f"[b]{item_id}[/b]\n"
        f"x: {int(pos_x)}  y: {int(pos_y)}\n"
        f"w: {int(width)}  h: {int(height)}"
    )


class LayoutDebugStatsBadge(FloatLayout):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("width", float(dp(152)))
        kwargs.setdefault("height", float(dp(58)))
        super().__init__(**kwargs)

        self.opacity = 0.0
        self.disabled = True

        with self.canvas.before:
            self._bg_color = Color(0.04, 0.05, 0.08, 0.94)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
            self._border_color = Color(0.72, 0.84, 1.0, 0.92)
            self._border_rect = Line(rectangle=(self.x, self.y, self.width, self.height), width=1.0)

        self.bind(pos=self._update_rects, size=self._update_rects)  # type: ignore[arg-type]

        self.label = Label(
            markup=True,
            halign="left",
            valign="top",
            size_hint=(1, 1),
            color=(1.0, 1.0, 1.0, 1.0),
            font_size="10sp",
            padding=(float(dp(6)), float(dp(5))),
        )
        self.label.bind(size=self._bind_text_size)  # type: ignore[arg-type]
        self.add_widget(self.label, index=len(self.children))

    def _bind_text_size(self, instance: Label, value: tuple[float, float]) -> None:
        instance.text_size = value

    def _update_rects(self, *_args: Any) -> None:
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        self._border_rect.rectangle = (self.x, self.y, self.width, self.height)

    def show_metrics(self, item_id: str, *, pos_x: float, pos_y: float, width: float, height: float) -> None:
        self.label.text = format_layout_debug_metrics(
            item_id,
            pos_x=pos_x,
            pos_y=pos_y,
            width=width,
            height=height,
        )
        self.opacity = 1.0
        self.disabled = False

    def hide(self) -> None:
        self.opacity = 0.0
        self.disabled = True
        self.label.text = ""


class DraggableLayoutWrapper(FloatLayout):
    def __init__(
        self,
        *,
        base: "OpenCiv",
        item_id: str,
        content: Widget,
        on_drag_end: PositionChangedCallback | None = None,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("pos_hint", {})
        super().__init__(**kwargs)

        self._base: "OpenCiv" = base
        self.item_id: str = item_id
        self.content: Widget = content
        self.on_drag_end: PositionChangedCallback | None = on_drag_end

        self.drag_enabled: bool = False
        self.overlay_enabled: bool = False
        self._dragging: bool = False
        self._drag_offset: tuple[float, float] = (0.0, 0.0)
        self._default_position: tuple[float, float] = (0.0, 0.0)
        self.handle_height: float = float(dp(22))

        self.add_widget(self.content, index=len(self.children))
        self._sync_content_geometry()

        self.content.bind(size=self._on_content_resize)  # type: ignore[arg-type]
        self.bind(size=self._on_wrapper_geometry_changed, pos=self._on_wrapper_geometry_changed)  # type: ignore[arg-type]

        with self.canvas.after:
            self._overlay_handle_color = Color(0.18, 0.4, 0.82, 0.0)
            self._overlay_handle_rect = Rectangle(pos=self.pos, size=(self.width, self.handle_height))
            self._overlay_outline_color = Color(0.75, 0.86, 1.0, 0.0)
            self._overlay_outline = Line(rectangle=(self.x, self.y, self.width, self.height), width=1.2)

        self.overlay_label = Label(
            size_hint=(None, None),
            height=self.handle_height,
            markup=True,
            halign="left",
            valign="middle",
            color=(1.0, 1.0, 1.0, 0.0),
            font_size="10sp",
        )
        self.overlay_label.bind(size=self._bind_overlay_text_size)  # type: ignore[arg-type]
        self.add_widget(self.overlay_label)

        self.stats_badge = LayoutDebugStatsBadge()
        self.add_widget(self.stats_badge)
        self._update_debug_chrome()

    def set_content(self, content: Widget) -> None:
        if self.content is content:
            self._sync_content_geometry()
            self._update_debug_chrome()
            return

        if getattr(self.content, "parent", None) is self:
            self.remove_widget(self.content)

        self.content = content
        self.add_widget(self.content, index=len(self.children))
        self.content.bind(size=self._on_content_resize)  # type: ignore[arg-type]
        self._sync_content_geometry()
        self._update_debug_chrome()

    def set_default_position(self, position: tuple[float, float]) -> None:
        self._default_position = position
        if not self.drag_enabled and not self.overlay_enabled:
            self.pos = position
            self._sync_content_geometry()
            self._update_debug_chrome()

    def reset_to_default_position(self) -> None:
        self.pos = self._default_position
        self._sync_content_geometry()
        self._update_debug_chrome()

    def set_drag_enabled(self, enabled: bool) -> None:
        self.drag_enabled = enabled
        self._update_debug_chrome()

    def set_overlay_enabled(self, enabled: bool) -> None:
        self.overlay_enabled = enabled
        self._update_debug_chrome()

    def apply_normalized_position(self, position: LayoutDebugPosition) -> None:
        self.pos = denormalize_position(position, self.get_window_size())
        self.clamp_to_parent_bounds()
        self._sync_content_geometry()
        self._update_debug_chrome()

    def get_normalized_position(self) -> LayoutDebugPosition:
        return normalize_position((float(self.x), float(self.y)), self.get_window_size())

    def get_window_size(self) -> tuple[float, float]:
        return (float(self._base.win.getXSize()), float(self._base.win.getYSize()))  # type: ignore[attr-defined]

    def _get_clamp_bounds(self) -> tuple[float, float]:
        window_width, window_height = self.get_window_size()
        if self.parent is None:
            return (window_width, window_height)

        parent_width = float(getattr(self.parent, "width", 0.0) or 0.0)
        parent_height = float(getattr(self.parent, "height", 0.0) or 0.0)

        return (max(window_width, parent_width), max(window_height, parent_height))

    def clamp_to_parent_bounds(self) -> None:
        clamp_width, clamp_height = self._get_clamp_bounds()
        clamped_x = clamp(float(self.x), 0.0, max(0.0, clamp_width - float(self.width)))
        clamped_y = clamp(float(self.y), 0.0, max(0.0, clamp_height - float(self.height)))
        self.pos = (clamped_x, clamped_y)

    def _on_wrapper_geometry_changed(self, *_args: Any) -> None:
        self._sync_content_geometry()
        self._update_debug_chrome()

    def _on_content_resize(self, *_args: Any) -> None:
        self.size = self.content.size
        self._sync_content_geometry()
        self.clamp_to_parent_bounds()
        self._update_debug_chrome()

    def _sync_content_geometry(self) -> None:
        self.size = self.content.size
        self.content.pos_hint = {}
        self.content.pos = self.pos

    def _bind_overlay_text_size(self, instance: Label, value: tuple[float, float]) -> None:
        instance.text_size = value

    def _touch_in_handle(self, touch_pos: tuple[float, float]) -> bool:
        return touch_pos[1] >= self.top - self.handle_height

    def _update_debug_chrome(self, *_args: Any) -> None:
        show_chrome = self.drag_enabled or self.overlay_enabled
        alpha = 0.72 if show_chrome else 0.0

        self._overlay_handle_color.rgba = (0.18, 0.4, 0.82, alpha)
        self._overlay_outline_color.rgba = (0.75, 0.86, 1.0, 0.85 if self.overlay_enabled else 0.0)
        self._overlay_handle_rect.pos = (self.x, self.top - self.handle_height)
        self._overlay_handle_rect.size = (self.width, self.handle_height)
        self._overlay_outline.rectangle = (self.x, self.y, self.width, self.height)

        self.overlay_label.size = (max(self.width - float(dp(8)), 0.0), self.handle_height)
        self.overlay_label.pos = (self.x + float(dp(4)), self.top - self.handle_height)
        self.overlay_label.color = (1.0, 1.0, 1.0, 1.0 if show_chrome else 0.0)
        self.overlay_label.text = (
            f"[b]{self.item_id}[/b] ({int(self.x)}, {int(self.y)})"
            if show_chrome
            else ""
        )

        badge_margin = float(dp(6))
        self.stats_badge.pos = (
            max(badge_margin, self.width - self.stats_badge.width - badge_margin),
            max(badge_margin, self.height - self.handle_height - self.stats_badge.height - badge_margin),
        )

        if self._dragging:
            self.stats_badge.show_metrics(
                self.item_id,
                pos_x=float(self.x),
                pos_y=float(self.y),
                width=float(self.width),
                height=float(self.height),
            )
        else:
            self.stats_badge.hide()

    def on_touch_down(self, touch: Any) -> bool:
        if self.drag_enabled and self.collide_point(*touch.pos) and self._touch_in_handle(touch.pos):
            touch.grab(self)
            self._dragging = True
            self._drag_offset = (float(touch.x - self.x), float(touch.y - self.y))
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch: Any) -> bool:
        if touch.grab_current is not self:
            return super().on_touch_move(touch)

        self.pos = (float(touch.x) - self._drag_offset[0], float(touch.y) - self._drag_offset[1])
        self.clamp_to_parent_bounds()
        self._update_debug_chrome()
        return True

    def on_touch_up(self, touch: Any) -> bool:
        if touch.grab_current is self:
            touch.ungrab(self)
            self._dragging = False
            self.clamp_to_parent_bounds()
            self._update_debug_chrome()
            if self.on_drag_end is not None:
                self.on_drag_end(self.item_id, (float(self.x), float(self.y)))
            return True
        return super().on_touch_up(touch)
