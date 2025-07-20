from typing import TYPE_CHECKING, Any, Dict

from gameplay.actions.debug.debug_action import DebugAction
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from managers.debug import DebugManager

if TYPE_CHECKING:
    from menus.screens.game_ui import GameUIScreen


class DebugActions:
    def __init__(self, screen: "GameUIScreen"):
        self.screen: "GameUIScreen" = screen
        self.is_open: bool = False

        self.frame: BoxLayout = BoxLayout(
            orientation="vertical", size_hint=(0.9, 0.9), pos_hint={"center_x": 0.5, "center_y": 0.5}
        )

        self.debug_manager: DebugManager = DebugManager.get_singleton_instance()

        with self.frame.canvas.before:
            Color(0.7, 0.7, 0.7, 1)
            self._bg_rect = Rectangle(pos=self.frame.pos, size=self.frame.size)
        self.frame.bind(pos=self._update_bg, size=self._update_bg)

        self.header: Widget = Widget(size_hint_y=None, height=dp(30))
        with self.header.canvas.before:  # type: ignore
            Color(0, 0, 0, 1)
            self._header_rect = Rectangle(pos=self.header.pos, size=self.header.size)  # type: ignore
        self.header.bind(pos=self._update_header, size=self._update_header)

        self.content: GridLayout = GridLayout(orientation="lr-tb", cols=3, spacing=dp(5), size_hint_y=None)
        self.buttons: Dict[str, Widget] = {}

        self.frame.add_widget(self.header)
        self.frame.add_widget(self.content)

    def build_buttons(self) -> None:
        actions: Dict[str, DebugAction] = self.debug_manager.get_all_debug_actions()
        for _, action in actions.items():
            btn: Widget = self._create_button(action)
            assert isinstance(btn, Widget), "Button creation failed"
            self.buttons[action.key] = btn
            self.content.add_widget(btn)

    def _create_button(self, action: DebugAction) -> Widget:
        btn = Button(
            text=action.key,
            size_hint_y=None,
            height=dp(40),
        )
        assert isinstance(btn, Button), "Button creation failed"
        btn.size_hint_y = None
        btn.height = dp(40)
        return btn

    def _update_bg(self, instance: Widget, value: Any) -> None:
        self._bg_rect.pos = instance.pos  # type: ignore
        self._bg_rect.size = instance.size  # type: ignore

    def _update_header(self, instance: Widget, value: Any) -> None:
        self._header_rect.pos = instance.pos  # type: ignore
        self._header_rect.size = instance.size  # type: ignore

    def show(self) -> None:
        if not self.buttons:
            self.build_buttons()

        self.frame.disabled = False
        self.frame.opacity = 1
        self.is_open = True

    def hide(self) -> None:
        self.frame.disabled = True
        self.frame.opacity = 0
        self.is_open = False
        self.current_entity = None
