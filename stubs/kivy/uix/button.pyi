from kivy.uix.widget import Widget
from kivy.uix.label import Label

from typing import Callable, Optional, Tuple

class Button(Label):
    def bind(
        self,
        on_release: Optional[Callable] = None,
        on_press: Optional[Callable] = None,
        size_hint: Optional[Tuple[int | None, int | None]] = None,
        size_hint_x: Optional[float] = None,
        size_hint_y: Optional[float] = None,
        height: Optional[int] = None,
        width: Optional[int] = None,
        **kwargs,
    ) -> None: ...
