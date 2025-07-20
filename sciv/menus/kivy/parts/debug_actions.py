from typing import TYPE_CHECKING, Any, Dict

from direct.showbase import MessengerGlobal
from gameplay.actions.debug.debug_action import DebugAction
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from managers.debug import DebugManager
from managers.i18n import t_

from sciv.system.actions import Action

if TYPE_CHECKING:
    from menus.screens.game_ui import GameUIScreen


class DebugActions:
    def __init__(self, screen: "GameUIScreen"):
        self.screen: "GameUIScreen" = screen
        self.is_open: bool = False

        self.frame: GridLayout = GridLayout(
            orientation="lr-tb", cols=3, spacing=dp(5), size_hint=(0.9, 0.9), pos_hint={"right": 0.95, "top": 0.95}
        )

        self.debug_manager: DebugManager = DebugManager.get_singleton_instance()

        with self.frame.canvas.before:
            Color(0.7, 0.7, 0.7, 1)
            self._bg_rect = Rectangle(pos=self.frame.pos, size=self.frame.size)  # type: ignore

        self.frame.bind(pos=self._update_bg, size=self._update_bg)

        self.buttons: Dict[str, Widget] = {}

    def build_buttons(self) -> None:
        actions: Dict[str, DebugAction] = self.debug_manager.get_all_debug_actions()
        for _, action in actions.items():
            btn: Widget = self._create_button(action)
            assert isinstance(btn, Widget), "Button creation failed"
            self.buttons[action.key] = btn
            self.frame.add_widget(btn)

    def _create_button(self, action: DebugAction) -> Widget:
        text: str = str(t_(key=action.name + ".button") if isinstance(action.name, str) else action.name)

        if action.targeting_tile_action:
            text += " (Tile Target)"
        elif action.targeting_unit_action:
            text += " (Unit Target)"

        btn = Button(
            text=text,
            size_hint_y=None,
            height=dp(40),
            width=dp(100),
        )
        btn.bind(on_release=lambda x, a=action: self.run_action(a))  # type: ignore
        assert isinstance(btn, Button), "Button creation failed"
        btn.size_hint_y = None
        btn.height = dp(40)
        return btn

    def run_action(self, action: Action) -> None:
        MessengerGlobal.messenger.send("ui.request.action.stage", [action])

    def _update_bg(self, instance: Widget, value: Any) -> None:
        self._bg_rect.pos = instance.pos  # type: ignore
        self._bg_rect.size = instance.size  # type: ignore

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
