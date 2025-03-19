from typing import Any, Callable, Dict, Optional
from kivy.uix.dropdown import DropDown
from kivy.lang import Builder
from kivy.config import Config
from menus.kivy.elements.button_value import ButtonValue
from kivy.uix.gridlayout import GridLayout


class ValueDropdown(DropDown):
    def __init__(
        self,
        text: str = "",
        k_v_pair: Dict[str, Any] = {},
        default_value: Optional[Any] = None,
        on_select: Optional[Callable] = None,
        **kwargs,
    ):
        self._win = None
        if "min_state_time" not in kwargs:
            self.min_state_time = float(Config.get("graphics", "min_state_time"))  # type: ignore
        if "container" not in kwargs:
            c = self.container = GridLayout(
                cols=1, height=44 * len(k_v_pair), spacing=0, padding=0
            )  # Ensure 1 column and dynamic rows
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

        self._on_select: Optional[Callable] = on_select
        self.auto_dismiss = False
        self.dismiss_on_select = False

        self.is_open: bool = False
        self.k_v_pair: Dict[str, Any] = k_v_pair
        self.text: str = text
        self.default_value: Optional[Any] = default_value
        self.own_button: Optional[ButtonValue] = None
        self.option_buttons: Dict[str, ButtonValue] = {}

        self.setup_main_button()

    def toggle_open(self, *args):
        if self.is_open:
            self.is_open = False
            self.dismiss_all()
        else:
            self.is_open = True
            self.open_all()

    def choose(self, instance: ButtonValue):
        if self.own_button is None:
            return

        if self.dismiss_on_select:
            self.dismiss()

        self.is_open = False
        self.dismiss_all()

        self.own_button.text = instance.text
        self.own_button.set_value(instance.get_value())

        if self._on_select is not None:
            self._on_select(instance)

    def setup_main_button(self):
        if self.own_button is None:
            self.own_button = ButtonValue(text=self.text, value=self.default_value)
            self.own_button.bind(on_release=self.toggle_open)
            self.container.add_widget(self.own_button)

    def calculate_height(self):
        self.container.height = sum(child.height for child in self.container.children)
        self.container.minimum_height = self.container.height

    def setup_values(self):
        self.option_buttons = {}
        for k, v in self.k_v_pair.items():
            btn = ButtonValue(text=k, value=v, size_hint_y=None, height=44, on_press=self.choose)
            self.container.add_widget(btn)  # Ensure buttons are added to container correctly
            self.option_buttons[k] = btn
        self.calculate_height()

    def dismiss_all(self):
        for btn in self.option_buttons.values():
            self.container.remove_widget(btn)
        if self.own_button is None:
            self.setup_main_button()
        self.calculate_height()

    def open_all(self):
        # Clear current widgets (this removes both own_button and container)
        self.clear_widgets()
        self.add_widget(self.own_button)
        # Recreate the option buttons inside the container
        self.setup_values()
        # Optionally update the dropdown size to match the container
        self.calculate_height()
