from kivy.uix.popup import Popup


class PopupDraggableMixin:
    dragging: bool = False
    _touch_offset = (0, 0)

    def transform_touch(self, touch):
        return touch

    def on_touch_down(self, touch):
        touch = self.transform_touch(touch)
        if hasattr(self, "collide_point") and self.collide_point(*touch.pos):  # type: ignore
            self.dragging = True
            self._touch_offset = (self.x - touch.x, self.y - touch.y)  # type: ignore
            return True
        return super().on_touch_down(touch)  # type: ignore

    def on_touch_move(self, touch):
        if self.dragging:
            touch = self.transform_touch(touch)
            self.pos = (touch.x + self._touch_offset[0], touch.y + self._touch_offset[1])
            return True
        return super().on_touch_move(touch)  # type: ignore

    def on_touch_up(self, touch):
        if self.dragging:
            self.dragging = False
            return True
        return super().on_touch_up(touch)  # type: ignore


class ModalPopup(Popup):
    pass


class DraggableModalPopup(ModalPopup, PopupDraggableMixin):
    def __init__(self, **kwargs):
        kwargs.setdefault("pos_hint", {})
        super().__init__(**kwargs)
