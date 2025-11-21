from typing import Any, Callable, Optional, Self

from menus.kivy.elements.styled import SecondaryButton


class ButtonValue(SecondaryButton):
    def __init__(
        self,
        value: Optional[Any] = None,
        on_press: Optional[Callable[[Self], Any]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        if args and "text" not in kwargs:
            kwargs["text"] = args[0]

        super().__init__(**kwargs)
        self.value: Optional[Any] = value
        self._on_press: Optional[Callable[[Self], Any]] = on_press

    def set_value(self, value: Optional[Any]) -> None:
        self.value = value

    def get_value(self) -> Optional[Any]:
        return self.value

    def action_dispatch(self) -> None:
        if self._on_press is not None:
            self._on_press(self)

    def on_press(self) -> None:
        if self._on_press is not None:
            self.action_dispatch()
