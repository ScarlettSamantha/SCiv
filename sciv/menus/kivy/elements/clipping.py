from typing import Any, List

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget


class ClippingScrollList(ScrollView):
    TOP = 1.0
    BOTTOM = 0.0

    def __init__(
        self,
        cols: int = 1,
        smooth_scroll_speed: float = 0.15,
        invert_scroll: bool = False,
        start_at_bottom: bool = False,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.do_scroll_x = False
        self.do_scroll_y = True

        self.smooth_scroll_speed: float = smooth_scroll_speed
        self.invert_scroll: bool = invert_scroll
        self.start_at_bottom: bool = start_at_bottom
        self.scroll_step_size = 30
        self.bar_width = 12
        self.bar_color: List[int] = [1, 1, 1, 1]

        self._container = GridLayout(cols=cols, size_hint_y=None, padding=5, spacing=5)
        self._container.bind(minimum_height=self._container.setter("height"))  # type: ignore

        super().add_widget(self._container)

        Clock.schedule_once(self._set_initial_scroll, 0)  # type: ignore
        Clock.schedule_once(self._apply_clipping, 0)  # type: ignore

    def _set_initial_scroll(self, dt: Any):
        if self.start_at_bottom:
            target = self.TOP if self.invert_scroll else self.BOTTOM
        else:
            target = self.BOTTOM if self.invert_scroll else self.TOP
        self.scroll_y = target

    def add_widget(self, widget: Widget, *args: Any, **kwargs: Any):
        if widget is self._container:
            super().add_widget(widget, *args, **kwargs)
        else:
            widget.opacity = 1
            self._container.add_widget(widget)
            Clock.schedule_once(self._apply_clipping, 0)  # type: ignore

    def scroll_to_top(self):
        target: float = 0.0 if self.invert_scroll else 1.0
        Animation(scroll_y=target, d=self.smooth_scroll_speed, t="out_cubic").start(self)  # type: ignore

    def scroll_to_bottom(self) -> None:
        target: float = 1.0 if self.invert_scroll else 0.0
        Animation(scroll_y=target, d=self.smooth_scroll_speed, t="out_cubic").start(self)  # type: ignore

    def scroll_by_step(self, direction: str = "up"):
        step: float = self._get_step_size()
        cur: float = self.scroll_y
        content_h: int = max(1, self._container.height)
        delta: float = step / content_h

        if (direction == "down") ^ self.invert_scroll:
            new = cur + delta
        else:
            new: float = cur - delta

        self.scroll_y = max(0.0, min(1.0, new))

    def _get_step_size(self) -> float:
        if self._container.children:
            return self._container.children[-1].height
        return self.scroll_step_size

    def smooth_scroll_to(self, target_widget: Widget):
        if target_widget not in self._container.children:
            return

        y: int | float = target_widget.y
        h: int = target_widget.height
        content_h: int = max(self._container.height, self.height)
        view_h: int = self.height

        if content_h > view_h:
            norm: float = 1.0 - ((y + h) / (content_h - view_h))
        else:
            norm = 1.0

        norm = max(0.0, min(1.0, norm))
        final: float = 1.0 - norm if self.invert_scroll else norm

        Animation(scroll_y=final, d=self.smooth_scroll_speed, t="out_cubic").start(self)  # type: ignore

    def force_scroll_to(self, target_widget: Widget):
        if target_widget not in self._container.children:
            return

        y: int | float = target_widget.y
        h: int = target_widget.height
        content_h: int = max(self._container.height, self.height)
        view_h: int = self.height

        if content_h > view_h:
            norm: float = 1.0 - ((y + h) / (content_h - view_h))
        else:
            norm = 1.0

        norm = max(0.0, min(1.0, norm))
        self.scroll_y = 0.0 + norm if self.invert_scroll else norm

    def clear_widgets(self, children: List[Widget] | None = None):
        self._container.clear_widgets(children=children)
        Clock.schedule_once(self._apply_clipping, 0)  # type: ignore

    def on_scroll_y(self, *args: Any):
        Clock.schedule_once(self._apply_clipping, 0)  # type: ignore

    def _apply_clipping(self, *args: Any):
        if not self._container.children:
            return

        self._container.do_layout()  # type: ignore
        content_h: int = self._container.height
        view_h: int = self.height
        self.do_scroll_y: bool = content_h > view_h

        wy = self.to_window(0, self.y)[1]
        top = wy + view_h

        for child in self._container.children:
            cy = child.to_window(0, child.y)[1] + child.height
            child.opacity = 1 if (cy > wy and cy <= top) else 0


class HorizontalClippingScrollList(ScrollView):
    def __init__(self, rows: int = 1, smooth_scroll_speed: float = 0.2, **kwargs: Any):
        super().__init__(**kwargs)  # type: ignore
        self.do_scroll_x = True
        self.do_scroll_y = False
        self.smooth_scroll_speed: float = smooth_scroll_speed

        self.bar_width = 12
        self.bar_color: List[int] = [1, 1, 1, 1]

        self._container = GridLayout(rows=rows, size_hint_x=None, padding=5, spacing=5)
        self._container.bind(minimum_width=self._container.setter("width"))  # type: ignore

        self.add_widget(self._container)
        Clock.schedule_once(self._apply_clipping, 0)  # type: ignore

    def add_widget(self, widget: Widget, *args: Any, **kwargs: Any):
        if widget != self._container:
            widget.opacity = 1
            self._container.add_widget(widget)
            Clock.schedule_once(self._apply_clipping, 0)  # type: ignore
        else:
            super().add_widget(widget, *args, **kwargs)  # type: ignore

    def on_scroll_x(self, *args: Any):
        Clock.schedule_once(self._apply_clipping, 0)  # type: ignore

    def force_scroll_to(self, target_widget: Widget):
        if target_widget not in self._container.children:
            return
        content_width = self._container.width  # type: ignore

        target_left: float = target_widget.x  # type: ignore
        visible_space: int = max(1, content_width - self.width)  # type: ignore

        new_scroll: float = target_left / float(visible_space)  # type: ignore
        self.scroll_x = max(0.0, min(1.0, new_scroll))  # type: ignore

    def smooth_scroll_to(self, target_widget: Widget):
        if target_widget not in self._container.children:
            return

        content_width: int = self._container.width  # type: ignore
        target_left: int | float = target_widget.x  # type: ignore
        visible_space: int = max(1, content_width - self.width)  # type: ignore

        new_scroll = target_left / float(visible_space)  # type: ignore
        new_scroll: float = max(0.0, min(1.0, new_scroll))  # type: ignore
        Animation(scroll_x=new_scroll, d=self.smooth_scroll_speed, t="out_quad").start(self)  # type: ignore

    def scroll_to_left(self):
        self.scroll_x = 0.0

    def scroll_to_right(self):
        self.scroll_x = 1.0

    def clear_widgets(self, children: List[Widget] | None = None) -> None:
        self._container.clear_widgets(children=children)
        Clock.schedule_once(self._apply_clipping, 0)  # type: ignore

    def _apply_clipping(self, *args: Any):
        if not self._container.children:
            return

        self._container.do_layout()  # type: ignore
        self._container.canvas.ask_update()

        content_width: int = self._container.width  # type: ignore
        viewport_width: int = self.width  # type: ignore

        self.do_scroll_x: bool = content_width > viewport_width  # type: ignore

        viewport_left = self.to_window(self.x, self.y)[0]  # type: ignore
        viewport_right = viewport_left + viewport_width  # type: ignore

        for child in self._container.children:
            child_left = child.to_window(child.x, child.y)[0]  # type: ignore
            child_right = child_left + child.width  # type: ignore

            is_visible = not (child_right < viewport_left or child_left > viewport_right)
            child.opacity = 1.0 if is_visible else 0.0
