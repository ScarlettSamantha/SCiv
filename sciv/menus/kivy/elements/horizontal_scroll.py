from kivy.input.motionevent import MotionEvent
from kivy.uix.scrollview import ScrollView


class HorizontalScrollView(ScrollView):
    def on_touch_down(self, touch: MotionEvent) -> bool:
        # Intercept mouse wheel events to scroll horizontally
        if "button" in touch.profile and touch.button in ("scrollup", "scrolldown"):  # type: ignore
            step = 0.1  # adjust as needed
            if touch.button == "scrollup":
                self.scroll_x = max(self.scroll_x - step, 0)  # type: ignore
            elif touch.button == "scrolldown":
                self.scroll_x = min(self.scroll_x + step, 1)  # type: ignore
            return True
        return super().on_touch_down(touch)
