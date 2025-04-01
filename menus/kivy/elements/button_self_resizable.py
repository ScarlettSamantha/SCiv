from typing import Any

from kivy.uix.button import Button


class SelfResizableButton(Button):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

        self.size_hint = (None, None)  # type: ignore
        self.bind(text=self._update_size)
        self._update_size(self, self.text)

    def _update_size(self, instance: Button, value: str) -> None:
        self.texture_update()  # type: ignore
        padding_x, padding_y = 20, 10
        self.size = (self.texture_size[0] + padding_x, self.texture_size[1] + padding_y)  # type: ignore
