from typing import List

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget


class ClippingScrollList(ScrollView):
    def __init__(self, cols: int = 1, **kwargs):
        super().__init__(**kwargs)

        self.do_scroll_x = False  # Only vertical scrolling
        self.do_scroll_y = True
        self.smooth_scroll_speed = 0.2  # Adjust speed (higher = slower)

        # Make scrollbar wider and white
        self.bar_width = 12
        self.bar_color = [1, 1, 1, 1]  # RGBA (White, fully opaque)

        # Use a GridLayout instead of BoxLayout
        self._container = GridLayout(cols=cols, size_hint_y=None, padding=5, spacing=5)
        self._container.bind(minimum_height=self._container.setter("height"))  # type: ignore # Ensure scrolling works

        self.add_widget(self._container)

        # Ensure clipping is applied after the widget is initialized
        Clock.schedule_once(self._apply_clipping, 0)

    def add_widget(self, widget, *args, **kwargs):
        if isinstance(widget, Widget) and widget != self._container:
            widget.opacity = 1  # Ensure all widgets start visible
            self._container.add_widget(widget)

            # Ensure clipping recalculates after a widget is added
            Clock.schedule_once(self._apply_clipping, 0)
        else:
            super().add_widget(widget, *args, **kwargs)

    def force_scroll_to(self, target_widget):
        """
        Instantly scroll to a specific widget inside the list.
        Corrects for Panda3D-Kivy's inverted Y-axis.
        """
        if target_widget not in self._container.children:
            return  # Ensure the target is inside the scroll list

        # Get widget position relative to the container
        target_y = target_widget.y  # Kivy's local Y position
        content_height = self._container.height  # Total height of all widgets

        # Calculate the correct `scroll_y` (flipping Y-axis)
        target_scroll = 1.0 - ((target_y + target_widget.height) / max(1, content_height))

        # Clamp scroll value between 0 and 1
        self.scroll_y = max(0, min(1, target_scroll))

    def on_scroll_y(self, *args):
        Clock.schedule_once(self._apply_clipping, 0)

    def smooth_scroll_to(self, target_widget):
        if target_widget not in self._container.children:  # type: ignore
            return  # Ensure the target is inside the scroll list

        target_y = target_widget.to_window(0, target_widget.y)[1]
        viewport_y = self.to_window(0, self.y)[1]

        scroll_distance = (target_y - viewport_y) / self.height
        target_scroll = max(0, min(1, self.scroll_y - scroll_distance))  # Keep within bounds

        Animation(scroll_y=target_scroll, d=self.smooth_scroll_speed, t="out_quad").start(self)

    def scroll_to_top(self):
        self.scroll_y = 0.9999  # This is a hack to force the scroll to the top, with 1 it will not show any items.

    def scroll_to_bottom(self):
        self.scroll_y = 0.0

    def _apply_clipping(self, *args):
        if not self._container.children:
            return  # Avoid processing if there are no children

        # Force the container to update its layout
        self._container.do_layout()
        self._container.canvas.ask_update()

        content_height = self._container.height
        viewport_height = self.height

        # Disable scrolling if content fits in viewport
        self.do_scroll_y = content_height > viewport_height

        # Get the viewport's Y position (corrected for Panda3D-Kivy inversion)
        viewport_y = self.to_window(0, self.y)[1] + viewport_height  # Inverted viewport Y

        for child in self._container.children:  # type: ignore
            child_y = child.to_window(0, child.y)[1] + child.height  # Adjust for Kivy-Panda inversion
            child_top = child_y  # The top edge of the widget

            # Correct visibility logic:
            is_visible = (child_top >= viewport_y - viewport_height) and (child_top < viewport_y)

            if is_visible and child.opacity == 0:
                child.opacity = 1
            elif not is_visible and child.opacity == 1:
                child.opacity = 0  # Smooth fade-out

    def on_size(self, *args):
        Clock.schedule_once(self._apply_clipping, 0)

    def clear_widgets(self, children: List[Widget] | None = None) -> None:
        self._container.clear_widgets(children=children)
        Clock.schedule_once(self._apply_clipping, 0)  # Re-check scroll enablement
