from typing import Any, Dict, List

from direct.showbase import DirectObject
from kivy.clock import Clock
from kivy.input.motionevent import MotionEvent
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from menus.kivy.elements.tooltip import TooltipBehavior, dp
from system.messenger import Message, Messenger

ICON = 64
PAD = 8


class MessageWidget(ButtonBehavior, BoxLayout, TooltipBehavior, DirectObject.DirectObject):
    def __init__(self, message: Message, icon_size: int = ICON, *args: Any, **kwargs: Dict[str, Any]):
        kwargs.setdefault("orientation", "vertical")  # type: ignore
        kwargs.setdefault("size_hint", (None, None))  # type: ignore
        kwargs.setdefault("size", (icon_size + 100, icon_size))  # type: ignore
        super().__init__(*args, **kwargs)  # type: ignore
        TooltipBehavior.__init__(self)

        self.tooltip_anchor_x = "left"
        self.tooltip_anchor_y = "top"

        self.message: Message = message
        icon: str | Image | None = self.message.get_icon()

        if isinstance(icon, str):
            self.icon = Image(source=icon, size_hint=(None, None), size=(icon_size, icon_size), opacity=1.0)
            self.tooltip_image_source = icon
        elif isinstance(icon, Image):
            self.icon = Image(size_hint=(None, None), size=(icon_size, icon_size), opacity=1.0)
            if icon.texture is not None:
                self.icon.texture = icon.texture
            else:
                self.icon.source = icon.source
                if self.icon.source:
                    self.tooltip_image_source = self.icon.source
        else:
            raise TypeError("message.icon must be a str path or a Kivy Image")

        self.add_widget(self.icon)
        self.tooltip_text = str(message.tooltip) if message.tooltip else ""

    def on_enter(self, *args: Any):
        TooltipBehavior.on_enter(self, *args)

    def on_leave(self, *args: Any):
        TooltipBehavior.on_leave(self, *args)

    def _inside(self, touch: MotionEvent) -> bool:
        if "win_pos" in getattr(touch, "profile", ()):
            wx, wy = touch.win_pos
        else:
            wx, wy = touch.pos
        lx, ly = self.to_widget(wx, wy, relative=False)

        return self.collide_point(lx, ly)  # type: ignore

    def on_close_request(self, *args: Any):
        if self.message.is_closable:
            self.message.hide()
            parent = self.parent
            if parent is not None:
                parent.remove_widget(self)

    def on_touch_down(self, touch: MotionEvent) -> Any:
        if not self._inside(touch):
            return super().on_touch_down(touch)  # type: ignore

        btn = getattr(touch, "button", "left")
        if btn == "right":
            if self.message.is_closable:
                self.on_close_request(touch)
            return True

        return super().on_touch_down(touch)  # type: ignore

    def on_touch_up(self, touch: MotionEvent) -> Any:
        if self._inside(touch) and getattr(touch, "button", "left") == "right":
            return True
        return super().on_touch_up(touch)  # type: ignore

    def on_press(self, *args: Any):
        if self.message.is_clickable and not self.message.is_disabled:
            self.message.execute_click(*args)
        if self.message.is_closable:
            self.on_close_request(*args)


class MessageRenderer(AnchorLayout, DirectObject.DirectObject):
    def __init__(self, messenger: Messenger, *args: Any, **kwargs: Dict[str, Any]):
        kwargs.setdefault("size_hint", (1, 1))  # type: ignore
        super().__init__(*args, **kwargs)

        self.messenger: Messenger = messenger
        self.anchor_x = "right"
        self.anchor_y = "bottom"

        self.padding = (0, 0, dp(10), dp(100))  # type: ignore

        self.box = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            spacing=PAD,
            padding=PAD,
        )
        self.box.width = ICON + PAD * 2
        self.box.bind(minimum_height=self.box.setter("height"))
        self.add_widget(self.box)

        Clock.schedule_interval(self.refresh, 5)
        self.accept("ui.update.ui.messenger.refresh", lambda *_: self.refresh(0))
        self.refresh(0)

    def refresh(self, dt: float) -> None:
        self.messenger.update(0)
        messages: List[Message] = self.messenger.get_visible_messages(auto_update_before=False)

        self.box.clear_widgets()
        if not messages:
            self.box.height = PAD * 2
            return

        for msg in messages:
            self.box.add_widget(MessageWidget(message=msg, icon_size=ICON))
