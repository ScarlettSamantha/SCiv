from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget


class ClippingScrollList(ScrollView):
    def __init__(self, **kwargs):
        self.do_scroll_x = False  # Only vertical scrolling
        self.do_scroll_y = True
        self.smooth_scroll_speed = 0.2  # Adjust speed (higher = slower)

        self._container = BoxLayout(orientation="vertical", size_hint_y=None, padding=5)
        self._container.bind(minimum_height=self._container.setter("height"))  # type: ignore

        super().__init__(**kwargs)
        self.add_widget(self._container)

    def add_widget(self, widget, *args, **kwargs):
        if isinstance(widget, Widget) and widget != self._container:
            widget.opacity = 1  # Ensure all widgets start visible
            self._container.add_widget(widget)
            self._apply_clipping()  # Ensure correct visibility
        else:
            super().add_widget(widget, *args, **kwargs)

    def on_scroll_y(self, *args):
        Clock.schedule_once(self._apply_clipping, 0)

    def smooth_scroll_to(self, target_widget):
        """
        Scroll smoothly to a specific widget inside the list.
        """
        if target_widget not in self._container.children:  # type: ignore
            return  # Ensure the target is inside the scroll list

        target_y = target_widget.to_window(0, target_widget.y)[1]
        viewport_y = self.to_window(0, self.y)[1]

        scroll_distance = (target_y - viewport_y) / self.height
        target_scroll = max(0, min(1, self.scroll_y - scroll_distance))  # Keep within bounds

        Animation(scroll_y=target_scroll, d=self.smooth_scroll_speed, t="out_quad").start(self)

    def _apply_clipping(self, *args):
        """
        Apply clipping so items:
        - Start **visible** in the viewport.
        - Become **hidden as soon as their top crosses above the viewport's top**.
        """
        viewport_y = self.to_window(0, self.y)[1] + self.height  # Invert viewport Y

        for child in self._container.children:  # type: ignore
            child_y = child.to_window(0, child.y)[1] + child.height  # Adjust for Kivy-Panda inversion
            child_top = child_y  # The top edge of the widget

            # Correct visibility logic:
            is_visible = (child_top >= viewport_y - self.height) and (child_top < viewport_y)

            if is_visible and child.opacity == 0:
                child.opacity = 1
            elif not is_visible and child.opacity == 1:
                child.opacity = 0  # Smooth fade-out

    def on_size(self, *args):
        """
        Ensure the clipping updates when resizing the widget.
        """
        self._apply_clipping()
