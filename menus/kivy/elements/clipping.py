from typing import Any, List

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget


class ClippingScrollList(ScrollView):
    def __init__(self, cols: int = 1, smooth_scroll_speed: float = 0.2, **kwargs: Any):
        super().__init__()  # type: ignore
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

    def on_scroll_y(self, *args: Any):
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

    def _apply_clipping(self, *args: Any):
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

    def clear_widgets(self, children: List[Widget] | None = None) -> None:
        self._container.clear_widgets(children=children)
        Clock.schedule_once(self._apply_clipping, 0)  # type: ignore


class HorizontalClippingScrollList(ScrollView):
    """
    A ScrollView that clips children horizontally. Uses a GridLayout (rows=1)
    and toggles widget opacity based on whether they are inside the visible viewport.
    """

    def __init__(self, rows: int = 1, smooth_scroll_speed: float = 0.2, **kwargs: Any):
        super().__init__(**kwargs)
        self.do_scroll_x = True  # Now we scroll horizontally
        self.do_scroll_y = False
        self.smooth_scroll_speed = smooth_scroll_speed

        # Make scrollbar wider and white
        self.bar_width = 12
        self.bar_color = [1, 1, 1, 1]

        # Set up a horizontal GridLayout. We bind its minimum_width -> container.width
        self._container = GridLayout(rows=rows, size_hint_x=None, padding=5, spacing=5)
        self._container.bind(minimum_width=self._container.setter("width"))

        self.add_widget(self._container)
        Clock.schedule_once(self._apply_clipping, 0)

    def add_widget(self, widget: Widget, *args: Any, **kwargs: Any):
        # Same logic: if the widget isn't the container, add to container
        if isinstance(widget, Widget) and widget != self._container:
            widget.opacity = 1
            self._container.add_widget(widget)
            Clock.schedule_once(self._apply_clipping, 0)
        else:
            super().add_widget(widget, *args, **kwargs)

    def on_scroll_x(self, *args: Any):
        # Whenever the scroll changes, re-check visibility
        Clock.schedule_once(self._apply_clipping, 0)

    def force_scroll_to(self, target_widget: Widget):
        """
        Instantly scroll so 'target_widget' is visible on the left side.
        """
        if target_widget not in self._container.children:
            return
        content_width = self._container.width
        # We want the left edge of 'target_widget' to align with the left edge of the visible area
        # so we compute the ratio to set 'scroll_x'.
        target_left = target_widget.x
        visible_space = max(1, content_width - self.width)
        # Convert absolute X in the container to a 0.0..1.0 scroll_x.
        new_scroll = target_left / float(visible_space)
        self.scroll_x = max(0.0, min(1.0, new_scroll))

    def smooth_scroll_to(self, target_widget: Widget):
        """
        Animate scrolling horizontally to 'target_widget'.
        """
        if target_widget not in self._container.children:
            return
        content_width = self._container.width
        target_left = target_widget.x
        visible_space = max(1, content_width - self.width)

        new_scroll = target_left / float(visible_space)
        new_scroll = max(0.0, min(1.0, new_scroll))
        Animation(scroll_x=new_scroll, d=self.smooth_scroll_speed, t="out_quad").start(self)

    def scroll_to_left(self):
        self.scroll_x = 0.0

    def scroll_to_right(self):
        self.scroll_x = 1.0

    def clear_widgets(self, children: List[Widget] | None = None) -> None:
        self._container.clear_widgets(children=children)
        Clock.schedule_once(self._apply_clipping, 0)

    def _apply_clipping(self, *args: Any):
        """
        Adjust the opacity of child widgets based on whether they're in the current
        horizontal viewport (i.e., visible horizontally or not).
        """
        if not self._container.children:
            return

        self._container.do_layout()
        self._container.canvas.ask_update()

        content_width = self._container.width
        viewport_width = self.width

        # Toggle horizontal scrolling based on total content size
        self.do_scroll_x = content_width > viewport_width

        # The left/right edges of the current visible "viewport"
        viewport_left = self.to_window(self.x, self.y)[0]
        viewport_right = viewport_left + viewport_width

        # For each child, figure out its absolute X coords and see if it's on screen
        for child in self._container.children:
            child_left = child.to_window(child.x, child.y)[0]
            child_right = child_left + child.width

            # Check if the widget is within the viewport's horizontal range
            is_visible = not (child_right < viewport_left or child_left > viewport_right)
            child.opacity = 1.0 if is_visible else 0.0
