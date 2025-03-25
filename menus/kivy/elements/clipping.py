from typing import List

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget


class ClippingScrollList(ScrollView):
    def __init__(self, cols: int = 1, smooth_scroll_speed: float = 0.2, **kwargs):
        super().__init__(**kwargs)
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
        Clock.schedule_once(self._apply_clipping, 0)

    def add_widget(self, widget, *args, **kwargs):
        if isinstance(widget, Widget) and widget != self._container:
            widget.opacity = 1  # Ensure all widgets start visible
            self._container.add_widget(widget)
            Clock.schedule_once(self._apply_clipping, 0)
        else:
            super().add_widget(widget, *args, **kwargs)

    def force_scroll_to(self, target_widget):
        if target_widget not in self._container.children:
            return
        target_y = target_widget.y
        content_height = self._container.height
        target_scroll = 1.0 - ((target_y + target_widget.height) / max(1, content_height))
        self.scroll_y = max(0, min(1, target_scroll))

    def on_scroll_y(self, *args):
        Clock.schedule_once(self._apply_clipping, 0)

    def smooth_scroll_to(self, target_widget):
        if target_widget not in self._container.children:  # type: ignore
            return
        target_y = target_widget.to_window(0, target_widget.y)[1]
        viewport_y = self.to_window(0, self.y)[1]
        scroll_distance = (target_y - viewport_y) / self.height
        target_scroll = max(0, min(1, self.scroll_y - scroll_distance))
        Animation(scroll_y=target_scroll, d=self.smooth_scroll_speed, t="out_quad").start(self)

    def scroll_to_top(self):
        self.scroll_y = 0.9999  # Hack to force scrolling to the top

    def scroll_to_bottom(self):
        self.scroll_y = 0.0

    def _apply_clipping(self, *args):
        if not self._container.children:
            return
        self._container.do_layout()
        self._container.canvas.ask_update()
        content_height = self._container.height
        viewport_height = self.height
        self.do_scroll_y = content_height > viewport_height
        viewport_y = self.to_window(0, self.y)[1] + viewport_height
        for child in self._container.children:  # type: ignore
            child_y = child.to_window(0, child.y)[1] + child.height
            is_visible = (child_y >= viewport_y - viewport_height) and (child_y < viewport_y)
            child.opacity = 1 if is_visible else 0

    def on_size(self, *args):
        Clock.schedule_once(self._apply_clipping, 0)

    def clear_widgets(self, children: List[Widget] | None = None) -> None:
        self._container.clear_widgets(children=children)
        Clock.schedule_once(self._apply_clipping, 0)
