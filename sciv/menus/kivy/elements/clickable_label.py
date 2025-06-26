from kivy.uix.label import Label
from kivy.input.motionevent import MotionEvent


class ClickableLabel(Label):
    __events__ = ("on_click",)

    def on_touch_down(self, touch: MotionEvent) -> bool:
        if self.collide_point(*touch.pos):  #  type: ignore
            self.dispatch("on_click")  #      type: ignore
            return True
        return super().on_touch_down(touch)  #  type: ignore

    def on_click(self):
        pass
