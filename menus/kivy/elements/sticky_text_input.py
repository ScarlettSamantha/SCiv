from kivy.uix.textinput import TextInput


class StickyTextInput(TextInput):
    def on_touch_up(self, touch) -> None | bool:
        retval = super().on_touch_up(touch)

        if "button" in touch.profile and touch.button == "left":
            self.focus = True

        return retval
