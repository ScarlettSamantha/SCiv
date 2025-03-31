from typing import Any, List

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget


class ClippingScrollList(ScrollView):
    def __init__(self, cols: int = 1, smooth_scroll_speed: float = 0.2, **kwargs: Any):
        super().__init__(**kwargs)  # type: ignore
        self.do_scroll_x = False  # Only vertical scrolling
        self.do_scroll_y = True
        self.smooth_scroll_speed = smooth_scroll_speed  # Set via init argument

        # Make scrollbar wider and white
        self.bar_width = 12
        self.bar_color = [1, 1, 1, 1]  # RGBA (White, fully opaque)

        # Use a GridLayout instead of BoxLayout
        self._container = GridLayout(cols=cols, size_hint_y=None, padding=5, spacing=5)
        self._container.bind(minimum_height=self._container.setter("height"))  # type: ignore

        self.add_widget(self._container)
        Clock.schedule_once(self._apply_clipping, 0)  # type: ignore

    def add_widget(self, widget: Widget, *args: Any, **kwargs: Any):
        if isinstance(widget, Widget) and widget != self._container:  # type: ignore
            widget.opacity = 1  # Ensure all widgets start visible
            self._container.add_widget(widget)  # type: ignore
            Clock.schedule_once(self._apply_clipping, 0)  # type: ignore
        else:
            super().add_widget(widget, *args, **kwargs)  # type: ignore

    def force_scroll_to(self, target_widget: Widget):
        if target_widget not in self._container.children:
            return
        target_y: int = target_widget.y  # type: ignore
        content_height: int = self._container.height  # type: ignore
        target_scroll: int = 1.0 - ((target_y + target_widget.height) / max(1, content_height))  # type: ignore
        self.scroll_y = max(0, min(1, target_scroll))  # type: ignore

    def on_scroll_y(self, _):
        Clock.schedule_once(self._apply_clipping, 0)  # type: ignore

    def smooth_scroll_to(self, target_widget: Widget):
        if target_widget not in self._container.children:  # type: ignore
            return
        target_y = target_widget.to_window(0, target_widget.y)[1]  # type: ignore
        viewport_y = self.to_window(0, self.y)[1]  # type: ignore
        scroll_distance = (target_y - viewport_y) / self.height  # type: ignore
        target_scroll = max(0, min(1, self.scroll_y - scroll_distance))  # type: ignore
        Animation(scroll_y=target_scroll, d=self.smooth_scroll_speed, t="out_quad").start(self)  # type: ignore

    def scroll_to_top(self):
        self.scroll_y = 0.9999  # Hack to force scrolling to the top

    def scroll_to_bottom(self):
        self.scroll_y = 0.0

    def _apply_clipping(self, _):
        if not self._container.children:
            return
        self._container.do_layout()  # type: ignore
        self._container.canvas.ask_update()
        content_height = self._container.height  # type: ignore
        viewport_height = self.height  # type: ignore
        self.do_scroll_y = content_height > viewport_height  # type: ignore
        viewport_y = self.to_window(0, self.y)[1] + viewport_height  # type: ignore
        for child in self._container.children:  # type: ignore
            child_y = child.to_window(0, child.y)[1] + child.height  # type: ignore
            is_visible = (child_y >= viewport_y - viewport_height) and (child_y < viewport_y)  # type: ignore
            child.opacity = 1 if is_visible else 0

    def on_size(self, _):
        Clock.schedule_once(self._apply_clipping, 0)  # type: ignore

    def clear_widgets(self, children: List[Widget] | None = None) -> None:
        self._container.clear_widgets(children=children)
        Clock.schedule_once(self._apply_clipping, 0)  # type: ignore
