from kivy.uix.dropdown import DropDown
from kivy.lang import Builder
from kivy.config import Config


class Dropdown(DropDown):
    def __init__(self, **kwargs):
        self._win = None
        if "min_state_time" not in kwargs:
            self.min_state_time = float(Config.get("graphics", "min_state_time"))  # type: ignore
        if "container" not in kwargs:
            c = self.container = Builder.load_string(_grid_kv)  # type: ignore  # noqa: F821
        else:
            c = None
        if "do_scroll_x" not in kwargs:
            self.do_scroll_x = False
        if "size_hint" not in kwargs:
            if "size_hint_x" not in kwargs:
                self.size_hint_x = None
            if "size_hint_y" not in kwargs:
                self.size_hint_y = None
        super(DropDown, self).__init__(**kwargs)
        if c is not None:
            super(DropDown, self).add_widget(c)
            self.on_container(self, c)

        self.bind(on_key_down=self.on_key_down, size=self._reposition)
        self.fbind("size", self._reposition)  # type: ignore
