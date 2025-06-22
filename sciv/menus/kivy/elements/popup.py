from typing import Any, Callable, Dict, Optional

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup

from helpers.cache import Cache
from managers.i18n import T_TranslationOrStr
from menus.kivy.mixins.collidable import CollisionPreventionMixin


class ModalPopup(Popup, CollisionPreventionMixin):
    def __init__(
        self,
        title: T_TranslationOrStr,
        message: T_TranslationOrStr,
        confirm_callback: Optional[Callable[[], None]] = None,
        cancel_callback: Optional[Callable[[], None]] = None,
        width: int = 950,
        height: int = 500,
        **kwargs: Dict[str, Any],
    ):
        # Remove custom keys before passing to Popup.
        kwargs.pop("message", None)
        kwargs.pop("confirm_callback", None)
        kwargs.pop("cancel_callback", None)
        kwargs.setdefault("auto_dismiss", False)  # type: ignore False positive

        title = str(title)
        message = str(message)

        self.base = Cache.get_showbase_instance()

        super().__init__(title=title, base=self.base, size=(width, height), size_hint=(0.30, 0.25), **kwargs)  # type: ignore

        self._message: str = message
        self._confirm_callback: Optional[Callable[[], None]] = confirm_callback
        self._cancel_callback: Optional[Callable[[], None]] = cancel_callback
        self.auto_dismiss = False

        self.confirm_button: Optional[Button] = None
        self.close_button: Optional[Button] = None

        self.accept_button: Optional[Button] = None
        self.decline_button: Optional[Button] = None

        self.button_layout: Optional[BoxLayout] = None
        self.layout: BoxLayout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        self.bind(on_open=self.on_open)  # type: ignore
        self.bind(on_dismiss=self.on_close)  # type: ignore

        self.layout.add_widget(Label(text=self._message))

        # Build button row
        self.button_layout = BoxLayout(orientation="horizontal", size_hint=(1, 0.3), spacing=10)
        if self._confirm_callback and self._cancel_callback:
            self.accept_button = Button(text="Accept")
            self.decline_button = Button(text="Decline")
            self.accept_button.bind(on_release=self._on_confirm)
            self.decline_button.bind(on_release=self._on_cancel)
            self.button_layout.add_widget(self.accept_button)
            self.button_layout.add_widget(self.decline_button)
        elif self._confirm_callback:
            self.confirm_btn = Button(text="Confirm")
            self.confirm_btn.bind(on_release=self._on_confirm)
            self.confirm_btn.disabled = True
            self.button_layout.add_widget(self.confirm_btn)
        else:
            self.close_btn = Button(text="Close")
            self.close_btn.bind(on_release=lambda _: self.dismiss())  # type: ignore
            self.close_btn.disabled = True
            self.button_layout.add_widget(self.close_btn)

        self.layout.add_widget(self.button_layout)
        self.content = self.layout  # A Popup must have only one widget as content

    def _on_confirm(self, *args: Any) -> None:
        if self._confirm_callback:
            self._confirm_callback()
        self.dismiss()  # type: ignore

    def _on_cancel(self, *args: Any) -> None:
        if self._cancel_callback:
            self._cancel_callback()
        self.dismiss()  # type: ignore

    def on_close(self, *args: Any, **kwargs: Any):
        self.close_btn.disabled = True
        self.unregister_non_collidable(self.layout)

    def on_open(self, *args: Any, **kwargs: Any):
        self.close_btn.disabled = False
        self.register_non_collidable(self.layout)


class NonModalPopup(ModalPopup):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.modal = False  # allow interaction with background
        self.auto_dismiss = True


class PopupDraggableMixin:
    dragging: bool = False
    _touch_offset = (0, 0)


# DraggableModalPopup: The popup itself is draggable.
# Make sure to disable pos_hint so we can manually set pos
class DraggableModalPopup(ModalPopup, PopupDraggableMixin):
    def __init__(self, **kwargs: Any):
        # Ensure no automatic positioning
        kwargs.setdefault("pos_hint", {})
        super().__init__(**kwargs)


# NonModalDraggablePopup: A non-modal draggable popup.
class NonModalDraggablePopup(NonModalPopup, PopupDraggableMixin):
    def __init__(self, **kwargs: Any):
        # Ensure no automatic positioning
        kwargs.setdefault("pos_hint", {})
        super().__init__(**kwargs)
