from kivy.input.motionevent import MotionEvent
from kivy.uix.scrollview import ScrollView


class HorizontalScrollView(ScrollView):
    def scroll_horizontal(self, direction: int | float, step: float = 0.08) -> bool:
        if direction == 0:
            return False

        previous_scroll_x = float(self.scroll_x)

        if direction < 0:
            self.scroll_x = max(previous_scroll_x - step, 0.0)
        else:
            self.scroll_x = min(previous_scroll_x + step, 1.0)

        return float(self.scroll_x) != previous_scroll_x

    def on_touch_down(self, touch: MotionEvent) -> bool:
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        if "button" in touch.profile and touch.button in ("scrollup", "scrolldown"):  # type: ignore[attr-defined]
            direction = -1 if touch.button == "scrollup" else 1  # type: ignore[attr-defined]
            self.scroll_horizontal(direction)
            return True

        return super().on_touch_down(touch)
