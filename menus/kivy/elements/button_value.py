from typing import Any, Callable, Optional, Self

from kivy.uix.button import Button


class ButtonValue(Button):
    def __init__(self, value: Optional[Any] = None, on_press: Optional[Callable] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value: Optional[Any] = value
        self._on_press: Optional[Callable[[Self]]] = on_press

    def set_value(self, value):
        self.value = value

    def get_value(self) -> Optional[Any]:
        return self.value

    def action_dispatch(self):
        if self._on_press is not None:
            self._on_press(self)

    def on_press(self):
        if self._on_press is not None:
            self.action_dispatch()
