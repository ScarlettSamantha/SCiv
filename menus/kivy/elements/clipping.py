from typing import Any, List

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget


class ClippingScrollList(ScrollView):
    """
    A vertical ScrollView that clips off‐screen children by setting their opacity.
    Supports smooth scrolling, step scrolling, inverted scroll direction, and configurable start position.
    """

    def __init__(
        self,
        cols: int = 1,
        smooth_scroll_speed: float = 0.15,
        invert_scroll: bool = False,
        start_at_bottom: bool = False,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        # Always vertical
        self.do_scroll_x = False
        self.do_scroll_y = True

        self.smooth_scroll_speed = smooth_scroll_speed
        self.invert_scroll = invert_scroll
        self.start_at_bottom = start_at_bottom
        self.scroll_step_size = 30  # fallback step if no children

        # Customize the scrollbar
        self.bar_width = 12
        self.bar_color = [1, 1, 1, 1]

        # Container for widgets
        self._container = GridLayout(cols=cols, size_hint_y=None, padding=5, spacing=5)
        self._container.bind(minimum_height=self._container.setter("height"))  # type: ignore

        # Add container as the only direct child
        super().add_widget(self._container)

        # Set initial scroll position and then apply clipping
        Clock.schedule_once(self._set_initial_scroll, 0)  # type: ignore
        Clock.schedule_once(self._apply_clipping, 0)  # type: ignore

    def _set_initial_scroll(self, dt: Any):
        """
        Position scroll at top or bottom according to start_at_bottom,
        taking invert_scroll into account.
        """
        if self.start_at_bottom:
            # bottom = 0.0 normally, 1.0 if inverted
            target = 1.0 if self.invert_scroll else 0.0
        else:
            # top = 1.0 normally, 0.0 if inverted
            target = 0.0 if self.invert_scroll else 1.0
        self.scroll_y = target

    def add_widget(self, widget: Widget, *args: Any, **kwargs: Any):
        # Route all non‐container adds into the container
        if widget is self._container:
            super().add_widget(widget, *args, **kwargs)
        else:
            widget.opacity = 1
            self._container.add_widget(widget)
            Clock.schedule_once(self._apply_clipping, 0)  # type: ignore

    def scroll_to_top(self):
        # Animate to the visual "top" (start_at_bottom doesn’t affect this)
        target = 0.0 if self.invert_scroll else 1.0
        Animation(scroll_y=target, d=self.smooth_scroll_speed, t="out_cubic").start(self)  # type: ignore

    def scroll_to_bottom(self) -> None:
        # Animate to the visual "bottom"
        target = 1.0 if self.invert_scroll else 0.0
        Animation(scroll_y=target, d=self.smooth_scroll_speed, t="out_cubic").start(self)  # type: ignore

    def scroll_by_step(self, direction: str = "up"):
        """
        Move one “step” (one child‐height or fallback) up or down.
        Respects invert_scroll by flipping the sense of up/down.
        """
        step = self._get_step_size()
        cur = self.scroll_y
        content_h = max(1, self._container.height)
        delta = step / content_h

        # XOR flips direction when inverted
        if (direction == "down") ^ self.invert_scroll:
            new = cur + delta
        else:
            new = cur - delta

        self.scroll_y = max(0.0, min(1.0, new))

    def _get_step_size(self) -> float:
        if self._container.children:
            return self._container.children[-1].height
        return self.scroll_step_size

    def smooth_scroll_to(self, target_widget: Widget):
        """
        Animate scroll to bring target_widget into view.
        """
        if target_widget not in self._container.children:
            return

        y = target_widget.y
        h = target_widget.height
        content_h = max(self._container.height, self.height)
        view_h = self.height

        if content_h > view_h:
            norm = 1.0 - ((y + h) / (content_h - view_h))
        else:
            norm = 1.0

        norm = max(0.0, min(1.0, norm))
        final = 1.0 - norm if self.invert_scroll else norm

        Animation(scroll_y=final, d=self.smooth_scroll_speed, t="out_cubic").start(self)  # type: ignore

    def force_scroll_to(self, target_widget: Widget):
        """
        Immediately jump scroll to bring target_widget into view.
        """
        if target_widget not in self._container.children:
            return

        y = target_widget.y
        h = target_widget.height
        content_h = max(self._container.height, self.height)
        view_h = self.height

        if content_h > view_h:
            norm = 1.0 - ((y + h) / (content_h - view_h))
        else:
            norm = 1.0

        norm = max(0.0, min(1.0, norm))
        self.scroll_y = 0.0 + norm if self.invert_scroll else norm

    def clear_widgets(self, children: List[Widget] | None = None):
        self._container.clear_widgets(children=children)
        Clock.schedule_once(self._apply_clipping, 0)  # type: ignore

    def on_scroll_y(self, *args: Any):
        # Re‐apply clipping whenever scroll changes
        Clock.schedule_once(self._apply_clipping, 0)  # type: ignore

    def _apply_clipping(self, *args: Any):
        """
        Hide any child outside the current viewport by setting opacity=0.
        """
        if not self._container.children:
            return

        self._container.do_layout()  # type: ignore
        content_h = self._container.height
        view_h = self.height
        self.do_scroll_y = content_h > view_h

        wy = self.to_window(0, self.y)[1]
        top = wy + view_h

        for child in self._container.children:
            cy = child.to_window(0, child.y)[1] + child.height
            child.opacity = 1 if (cy > wy and cy <= top) else 0


class HorizontalClippingScrollList(ScrollView):
    def __init__(self, rows: int = 1, smooth_scroll_speed: float = 0.2, **kwargs: Any):
        super().__init__(**kwargs)  # type: ignore
        self.do_scroll_x = True  # Now we scroll horizontally
        self.do_scroll_y = False
        self.smooth_scroll_speed = smooth_scroll_speed

        # Make scrollbar wider and white
        self.bar_width = 12
        self.bar_color = [1, 1, 1, 1]

        # Set up a horizontal GridLayout. We bind its minimum_width -> container.width
        self._container = GridLayout(rows=rows, size_hint_x=None, padding=5, spacing=5)
        self._container.bind(minimum_width=self._container.setter("width"))  # type: ignore

        self.add_widget(self._container)
        Clock.schedule_once(self._apply_clipping, 0)  # type: ignore

    def add_widget(self, widget: Widget, *args: Any, **kwargs: Any):
        # Same logic: if the widget isn't the container, add to container
        if widget != self._container:
            widget.opacity = 1
            self._container.add_widget(widget)
            Clock.schedule_once(self._apply_clipping, 0)  # type: ignore
        else:
            super().add_widget(widget, *args, **kwargs)  # type: ignore

    def on_scroll_x(self, *args: Any):
        # Whenever the scroll changes, re-check visibility
        Clock.schedule_once(self._apply_clipping, 0)  # type: ignore

    def force_scroll_to(self, target_widget: Widget):
        """
        Instantly scroll so 'target_widget' is visible on the left side.
        """
        if target_widget not in self._container.children:
            return
        content_width = self._container.width  # type: ignore
        # We want the left edge of 'target_widget' to align with the left edge of the visible area
        # so we compute the ratio to set 'scroll_x'.
        target_left: float = target_widget.x  # type: ignore
        visible_space: int = max(1, content_width - self.width)  # type: ignore
        # Convert absolute X in the container to a 0.0..1.0 scroll_x.
        new_scroll: float = target_left / float(visible_space)  # type: ignore
        self.scroll_x = max(0.0, min(1.0, new_scroll))  # type: ignore

    def smooth_scroll_to(self, target_widget: Widget):
        if target_widget not in self._container.children:
            return

        content_width = self._container.width  # type: ignore
        target_left = target_widget.x  # type: ignore
        visible_space = max(1, content_width - self.width)  # type: ignore

        new_scroll = target_left / float(visible_space)  # type: ignore
        new_scroll = max(0.0, min(1.0, new_scroll))  # type: ignore
        Animation(scroll_x=new_scroll, d=self.smooth_scroll_speed, t="out_quad").start(self)  # type: ignore

    def scroll_to_left(self):
        self.scroll_x = 0.0

    def scroll_to_right(self):
        self.scroll_x = 1.0

    def clear_widgets(self, children: List[Widget] | None = None) -> None:
        self._container.clear_widgets(children=children)
        Clock.schedule_once(self._apply_clipping, 0)  # type: ignore

    def _apply_clipping(self, *args: Any):
        """
        Adjust the opacity of child widgets based on whether they're in the current
        horizontal viewport (i.e., visible horizontally or not).
        """
        if not self._container.children:
            return

        self._container.do_layout()  # type: ignore
        self._container.canvas.ask_update()

        content_width = self._container.width  # type: ignore
        viewport_width = self.width  # type: ignore

        # Toggle horizontal scrolling based on total content size
        self.do_scroll_x = content_width > viewport_width  # type: ignore

        # The left/right edges of the current visible "viewport"
        viewport_left = self.to_window(self.x, self.y)[0]  # type: ignore
        viewport_right = viewport_left + viewport_width  # type: ignore

        # For each child, figure out its absolute X coords and see if it's on screen
        for child in self._container.children:
            child_left = child.to_window(child.x, child.y)[0]  # type: ignore
            child_right = child_left + child.width  # type: ignore

            # Check if the widget is within the viewport's horizontal range
            is_visible = not (child_right < viewport_left or child_left > viewport_right)
            child.opacity = 1.0 if is_visible else 0.0
