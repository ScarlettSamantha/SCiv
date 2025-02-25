from typing import Any, Optional
from kivy.uix.button import Button


class ButtonValue(Button):
    def __init__(self, value: Optional[Any] = None, **kwargs):
        super().__init__(**kwargs)
        self.value: Optional[Any] = value

    def set_value(self, value):
        self.value = value

    def get_value(self) -> Optional[Any]:
        return self.value
