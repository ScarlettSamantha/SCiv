from typing import Any, Callable, Optional, Tuple, cast

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout

from helpers.cache import Cache
from managers.config import ConfigManager
from managers.i18n import T_TranslationOrStr
from menus.kivy.elements.layout_debug import LayoutDebugPosition, LayoutDebugStatsBadge, denormalize_position
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
        **kwargs: Any,
    ):
        kwargs.pop("message", None)
        kwargs.pop("confirm_callback", None)
        kwargs.pop("cancel_callback", None)
        kwargs.setdefault("auto_dismiss", False)
        kwargs.setdefault("size_hint", (0.30, 0.25))
        kwargs.setdefault("size", (width, height))

        title = str(title)
        message = str(message)

        self.base = Cache.get_showbase_instance()

        super().__init__(title=title, base=self.base, **kwargs)  # type: ignore

        self._message: str = message
        self._confirm_callback: Optional[Callable[[], None]] = confirm_callback
        self._cancel_callback: Optional[Callable[[], None]] = cancel_callback
        self.auto_dismiss = False

        self.confirm_button: Optional[Button] = None
        self.close_button: Optional[Button] = None
        self.accept_button: Optional[Button] = None
        self.decline_button: Optional[Button] = None
        self.confirm_btn: Optional[Button] = None
        self.close_btn: Optional[Button] = None
        self.button_layout: Optional[BoxLayout] = None

        self.content_root: RelativeLayout = RelativeLayout(size_hint=(1, 1))
        self.layout: BoxLayout = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(10),
            size_hint=(1, 1),
        )

        self.message_label = Label(
            text=self._message,
            halign="center",
            valign="middle",
            markup=True,
            size_hint=(1, 1),
        )
        self.message_label.bind(size=self._sync_label_text_size)  # type: ignore[arg-type]

        self.bind(on_open=self.on_open)  # type: ignore
        self.bind(on_dismiss=self.on_close)  # type: ignore

        self.layout.add_widget(self.message_label)

        self.button_layout = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(48),
            spacing=dp(10),
        )

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
        self.content_root.add_widget(self.layout)
        self.content = self.content_root

    @staticmethod
    def _sync_label_text_size(instance: Label, value: Tuple[float, float]) -> None:
        instance.text_size = (max(0.0, value[0] - float(dp(12))), value[1])

    def _on_confirm(self, *args: Any) -> None:
        if self._confirm_callback:
            self._confirm_callback()
        self.dismiss()  # type: ignore

    def _on_cancel(self, *args: Any) -> None:
        if self._cancel_callback:
            self._cancel_callback()
        self.dismiss()  # type: ignore

    def on_close(self, *args: Any, **kwargs: Any):
        if self.close_btn is not None:
            self.close_btn.disabled = True
        if self.confirm_btn is not None:
            self.confirm_btn.disabled = True
        self.unregister_non_collidable(self.layout)

    def on_open(self, *args: Any, **kwargs: Any):
        if self.close_btn is not None:
            self.close_btn.disabled = False
        if self.confirm_btn is not None:
            self.confirm_btn.disabled = False
        self.register_non_collidable(self.layout)


class NonModalPopup(ModalPopup):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.modal = False
        self.auto_dismiss = True


class PopupDraggableMixin:
    dragging: bool = False
    _touch_offset = (0, 0)

    def _popup_widget(self) -> Popup:
        return cast(Popup, self)

    def _init_layout_debug_drag(self, item_id: str) -> None:
        self._layout_debug_item_id: str = item_id
        self._layout_debug_config: ConfigManager = ConfigManager.get_singleton_instance()
        self._layout_debug_drag_position_initialized: bool = False
        self._layout_debug_badge = LayoutDebugStatsBadge()
        cast(ModalPopup, self).content_root.add_widget(self._layout_debug_badge)
        self._layout_debug_badge.hide()

    def _layout_debug_drag_enabled(self) -> bool:
        return self._layout_debug_config.get_debug_mode() and self._layout_debug_config.get_ui_layout_drag_enabled()

    def _layout_debug_saved_position(self) -> LayoutDebugPosition | None:
        data = self._layout_debug_config.get_ui_layout_position(self._layout_debug_item_id)
        if data is None:
            return None
        return LayoutDebugPosition(x=float(data.get("x", 0.0)), y=float(data.get("y", 0.0)))

    def _layout_debug_window_size(self) -> Tuple[float, float]:
        base = cast(Any, self).base
        return (float(base.win.getXSize()), float(base.win.getYSize()))  # type: ignore[attr-defined]

    def _layout_debug_clamp_position(self, pos_x: float, pos_y: float) -> Tuple[float, float]:
        window_width, window_height = self._layout_debug_window_size()
        popup = self._popup_widget()

        return (
            max(0.0, min(pos_x, window_width - float(popup.width))),
            max(0.0, min(pos_y, window_height - float(popup.height))),
        )

    def _layout_debug_apply_initial_position(self) -> None:
        if self._layout_debug_drag_position_initialized:
            return

        popup = self._popup_widget()
        popup.pos_hint = {}

        saved_position = self._layout_debug_saved_position()
        if saved_position is not None:
            saved_x, saved_y = denormalize_position(saved_position, self._layout_debug_window_size())
            popup.pos = self._layout_debug_clamp_position(saved_x, saved_y)
        else:
            window_width, window_height = self._layout_debug_window_size()
            centered_x = (window_width - float(popup.width)) / 2.0
            centered_y = (window_height - float(popup.height)) / 2.0
            popup.pos = self._layout_debug_clamp_position(centered_x, centered_y)

        self._layout_debug_drag_position_initialized = True

    def _layout_debug_store_position(self) -> None:
        window_width, window_height = self._layout_debug_window_size()
        popup = self._popup_widget()

        self._layout_debug_config.set_ui_layout_position(
            self._layout_debug_item_id,
            float(popup.x) / max(window_width, 1.0),
            float(popup.y) / max(window_height, 1.0),
        )

    def _layout_debug_update_badge(self) -> None:
        popup = self._popup_widget()
        content_root = cast(ModalPopup, self).content_root
        badge_margin = float(dp(8))

        self._layout_debug_badge.pos = (
            max(badge_margin, float(content_root.width) - float(self._layout_debug_badge.width) - badge_margin),
            max(badge_margin, float(content_root.height) - float(self._layout_debug_badge.height) - badge_margin),
        )

        if self.dragging:
            self._layout_debug_badge.show_metrics(
                self._layout_debug_item_id,
                pos_x=float(popup.x),
                pos_y=float(popup.y),
                width=float(popup.width),
                height=float(popup.height),
            )
        else:
            self._layout_debug_badge.hide()

    def _layout_debug_touch_in_handle(self, touch_pos: Tuple[float, float]) -> bool:
        return touch_pos[1] >= float(self._popup_widget().top) - float(dp(36))


class DraggableModalPopup(ModalPopup, PopupDraggableMixin):
    def __init__(self, **kwargs: Any):
        item_id = str(kwargs.pop("layout_debug_id", "popup.modal"))
        kwargs.setdefault("pos_hint", {})
        super().__init__(**kwargs)
        self._init_layout_debug_drag(item_id)

    def on_open(self, *args: Any, **kwargs: Any):
        super().on_open(*args, **kwargs)
        self._layout_debug_apply_initial_position()
        self._layout_debug_update_badge()

    def on_touch_down(self, touch: Any) -> bool:
        if self._layout_debug_drag_enabled() and self.collide_point(*touch.pos) and self._layout_debug_touch_in_handle(touch.pos):
            touch.grab(self)
            self.dragging = True
            self._touch_offset = (float(touch.x - self.x), float(touch.y - self.y))
            self._layout_debug_update_badge()
            return True

        return super().on_touch_down(touch)

    def on_touch_move(self, touch: Any) -> bool:
        if touch.grab_current is self:
            self.pos = self._layout_debug_clamp_position(
                float(touch.x) - float(self._touch_offset[0]),
                float(touch.y) - float(self._touch_offset[1]),
            )
            self._layout_debug_update_badge()
            return True

        return super().on_touch_move(touch)

    def on_touch_up(self, touch: Any) -> bool:
        if touch.grab_current is self:
            touch.ungrab(self)
            self.dragging = False
            self._layout_debug_store_position()
            self._layout_debug_update_badge()
            return True

        return super().on_touch_up(touch)


class NonModalDraggablePopup(NonModalPopup, PopupDraggableMixin):
    def __init__(self, **kwargs: Any):
        item_id = str(kwargs.pop("layout_debug_id", "popup.non_modal"))
        kwargs.setdefault("pos_hint", {})
        super().__init__(**kwargs)
        self._init_layout_debug_drag(item_id)

    def on_open(self, *args: Any, **kwargs: Any):
        super().on_open(*args, **kwargs)
        self._layout_debug_apply_initial_position()
        self._layout_debug_update_badge()

    def on_touch_down(self, touch: Any) -> bool:
        if self._layout_debug_drag_enabled() and self.collide_point(*touch.pos) and self._layout_debug_touch_in_handle(touch.pos):
            touch.grab(self)
            self.dragging = True
            self._touch_offset = (float(touch.x - self.x), float(touch.y - self.y))
            self._layout_debug_update_badge()
            return True

        return super().on_touch_down(touch)

    def on_touch_move(self, touch: Any) -> bool:
        if touch.grab_current is self:
            self.pos = self._layout_debug_clamp_position(
                float(touch.x) - float(self._touch_offset[0]),
                float(touch.y) - float(self._touch_offset[1]),
            )
            self._layout_debug_update_badge()
            return True

        return super().on_touch_move(touch)

    def on_touch_up(self, touch: Any) -> bool:
        if touch.grab_current is self:
            touch.ungrab(self)
            self.dragging = False
            self._layout_debug_store_position()
            self._layout_debug_update_badge()
            return True

        return super().on_touch_up(touch)
