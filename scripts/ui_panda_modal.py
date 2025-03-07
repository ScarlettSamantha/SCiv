from direct.showbase.ShowBase import ShowBase
from kivy.config import Config
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from panda3d_kivy.app import App

Config.set("input", "mouse", "mouse,multitouch_on_demand")


class PopupDraggableMixin:
    dragging: bool = False
    _touch_offset = (0, 0)

    def transform_touch(self, touch):
        return touch

    def on_touch_down(self, touch):
        touch = self.transform_touch(touch)
        if self.collide_point(*touch.pos):
            self.dragging = True
            self._touch_offset = (self.x - touch.x, self.y - touch.y)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.dragging:
            touch = self.transform_touch(touch)
            self.pos = (touch.x + self._touch_offset[0], touch.y + self._touch_offset[1])
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.dragging:
            self.dragging = False
            return True
        return super().on_touch_up(touch)


class ModalPopup(Popup):
    pass


class DraggableModalPopup(ModalPopup, PopupDraggableMixin):
    def __init__(self, **kwargs):
        kwargs.setdefault("pos_hint", {})
        super().__init__(**kwargs)


class TestApp(App):
    def build(self):
        root = BoxLayout(orientation="vertical", padding=20, spacing=20)
        btn_draggable_modal = Button(text="Open Draggable Modal Popup", size_hint=(1, 0.2))
        btn_draggable_modal.bind(on_release=self.open_draggable_modal_popup)
        root.add_widget(btn_draggable_modal)
        return root

    def open_draggable_modal_popup(self, instance: Button) -> None:
        popup = DraggableModalPopup(
            title="Draggable Modal Popup",
            message="This modal popup is draggable (panda3d-kivy).",
            size_hint=(None, None),
            size=(400, 300),
        )
        popup.pos = (200, 200)
        popup.open()


class MyPandaApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.kivy_app = TestApp(self)
        self.embed = App(self.kivy_app)


if __name__ == "__main__":
    app = MyPandaApp()
    app.run()
