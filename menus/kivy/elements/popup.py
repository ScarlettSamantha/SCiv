# Base modal popup with title, message, and 1 or 2 buttons.
from typing import Callable, Optional

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup

from managers.i18n import T_TranslationOrStr, T_TranslationOrStrOrNone


class ModalPopup(Popup):
    def __init__(
        self,
        title: T_TranslationOrStr,
        message: T_TranslationOrStr,
        confirm_callback: Optional[Callable[[], None]] = None,
        cancel_callback: Optional[Callable[[], None]] = None,
        width: int = 950,
        height: int = 500,
        **kwargs,
    ):
        # Remove custom keys before passing to Popup.
        kwargs.pop("message", None)
        kwargs.pop("confirm_callback", None)
        kwargs.pop("cancel_callback", None)
        kwargs.setdefault("auto_dismiss", False)

        if isinstance(title, T_TranslationOrStr | T_TranslationOrStrOrNone):
            title = str(title)
        if isinstance(message, T_TranslationOrStr | T_TranslationOrStrOrNone):
            message = str(message)

        super().__init__(title=title, size=(width, height), size_hint=(0.30, 0.25), **kwargs)

        self._message: str = message
        self._confirm_callback: Optional[Callable] = confirm_callback
        self._cancel_callback: Optional[Callable] = cancel_callback
        self.auto_dismiss = False

        # Build a simple layout.
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Show the message
        layout.add_widget(Label(text=self._message))

        # Build button row
        btn_layout = BoxLayout(orientation="horizontal", size_hint=(1, 0.3), spacing=10)
        if self._confirm_callback and self._cancel_callback:
            accept_btn = Button(text="Accept")
            decline_btn = Button(text="Decline")
            accept_btn.bind(on_release=lambda _: self._on_confirm())
            decline_btn.bind(on_release=lambda _: self._on_cancel())
            btn_layout.add_widget(accept_btn)
            btn_layout.add_widget(decline_btn)
        elif self._confirm_callback:
            confirm_btn = Button(text="Confirm")
            confirm_btn.bind(on_release=lambda _: self._on_confirm())
            btn_layout.add_widget(confirm_btn)
        else:
            close_btn = Button(text="Close")
            close_btn.bind(on_release=lambda _: self.dismiss())
            btn_layout.add_widget(close_btn)

        layout.add_widget(btn_layout)
        self.content = layout  # A Popup must have only one widget as content

    def _on_confirm(self) -> None:
        if self._confirm_callback:
            self._confirm_callback()
        self.dismiss()

    def _on_cancel(self) -> None:
        if self._cancel_callback:
            self._cancel_callback()
        self.dismiss()


# Non-modal popup: simply a ModalPopup with modal behavior turned off.
class NonModalPopup(ModalPopup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.modal = False  # allow interaction with background
        self.auto_dismiss = True


class PopupDraggableMixin:
    dragging: bool = False
    _touch_offset = (0, 0)

    def on_touch_down(self, touch):
        # Add a debug print to see if this method is called
        print("[DEBUG] on_touch_down, collide=", self.collide_point(*touch.pos), "pos=", self.pos, "touch=", touch.pos)
        if self.collide_point(*touch.pos):
            self.dragging = True
            self._touch_offset = (self.x - touch.x, self.y - touch.y)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.dragging:
            # Another debug print to confirm movement
            print(
                "[DEBUG] on_touch_move, new popup pos=",
                (touch.x + self._touch_offset[0], touch.y + self._touch_offset[1]),
            )
            self.pos = (touch.x + self._touch_offset[0], touch.y + self._touch_offset[1])
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.dragging:
            print("[DEBUG] on_touch_up, stopping drag")
            self.dragging = False
            return True
        return super().on_touch_up(touch)


# DraggableModalPopup: The popup itself is draggable.
# Make sure to disable pos_hint so we can manually set pos
class DraggableModalPopup(ModalPopup, PopupDraggableMixin):
    def __init__(self, **kwargs):
        # Ensure no automatic positioning
        kwargs.setdefault("pos_hint", {})
        super().__init__(**kwargs)


# NonModalDraggablePopup: A non-modal draggable popup.
class NonModalDraggablePopup(NonModalPopup, PopupDraggableMixin):
    def __init__(self, **kwargs):
        # Ensure no automatic positioning
        kwargs.setdefault("pos_hint", {})
        super().__init__(**kwargs)
