from typing import TYPE_CHECKING, Any, Dict, List, Optional

from direct.showbase import MessengerGlobal
from gameplay.actions.debug.debug_action import DebugAction
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from managers.debug import DebugManager
from managers.i18n import t_
from system.actions import Action

if TYPE_CHECKING:
    from menus.screens.game_ui import GameUIScreen


class DebugActions:
    def __init__(self, screen: "GameUIScreen"):
        self.screen: "GameUIScreen" = screen
        self.is_open: bool = False
        window_width = float(self.screen._base.win.getXSize())  # type: ignore[attr-defined]
        window_height = float(self.screen._base.win.getYSize())  # type: ignore[attr-defined]

        self.frame: GridLayout = GridLayout(
            cols=1,
            spacing=dp(8),
            padding=dp(8),
            size_hint=(None, None),
            width=window_width * 0.82,
            height=window_height * 0.82,
            pos=(window_width * 0.09, window_height * 0.09),
        )

        self.debug_manager: DebugManager = DebugManager.get_singleton_instance()

        with self.frame.canvas.before:
            Color(0.04, 0.04, 0.06, 0.92)
            self._bg_rect = Rectangle(pos=self.frame.pos, size=self.frame.size)  # type: ignore

        self.frame.bind(pos=self._update_bg, size=self._update_bg)

        self.buttons: Dict[str, Widget] = {}

    def build_buttons(self) -> None:
        actions: Dict[str, DebugAction] = self.debug_manager.get_all_debug_actions()

        categories: Dict[Optional[str], List[DebugAction]] = {}
        for action in actions.values():
            category: Optional[str] = getattr(action, "category", None)
            if category not in categories:
                categories[category] = []
            categories[category].append(action)

        def sort_category_key(value: Optional[str]) -> tuple[bool, str]:
            if value is None:
                return True, ""
            return False, value.lower()

        for category in sorted(categories.keys(), key=sort_category_key):
            header: Widget = self._create_category_header(category)
            self.frame.add_widget(header)

            row_layout: GridLayout = GridLayout(
                cols=3,
                spacing=dp(5),
                size_hint_y=None,
            )
            row_layout.bind(minimum_height=row_layout.setter("height"))  # type: ignore

            for action in sorted(categories[category], key=lambda a: str(a.name)):
                btn: Widget = self._create_button(action)
                self.buttons[action.key] = btn
                row_layout.add_widget(btn)

            self.frame.add_widget(row_layout)

    def _create_category_header(self, category: Optional[str]) -> Widget:
        title: str = category if category else "General"
        label: Label = Label(
            text=f"[b]{title}[/b]",
            markup=True,
            size_hint_y=None,
            height=dp(26),
            halign="left",
            valign="middle",
            padding=(dp(4), dp(2)),
        )
        label.bind(size=self._update_header_text_size)

        with label.canvas.before:  # type: ignore
            Color(0.15, 0.17, 0.22, 1)
            Rectangle(pos=label.pos, size=label.size)  # type: ignore

        label.bind(pos=self._update_header_bg, size=self._update_header_bg)
        return label

    def _update_header_text_size(self, instance: Label, value: Any) -> None:
        instance.text_size = value  # type: ignore

    def _update_header_bg(self, instance: Widget, value: Any) -> None:
        for instr in instance.canvas.before.children:  # type: ignore
            if isinstance(instr, Rectangle):
                instr.pos = instance.pos  # type: ignore
                instr.size = instance.size  # type: ignore

    def _create_button(self, action: DebugAction) -> Widget:
        text: str = str(t_(key=action.name + ".button") if isinstance(action.name, str) else action.name)

        if action.targeting_tile_action:
            text += " (Tile Target)"
        elif action.targeting_unit_action:
            text += " (Unit Target)"

        btn: Button = Button(
            text=text,
            size_hint_y=None,
            height=dp(40),
            width=dp(120),
        )
        btn.bind(on_release=lambda x, a=action: self.run_action(a))  # type: ignore
        return btn

    def run_action(self, action: Action) -> None:
        MessengerGlobal.messenger.send("ui.request.action.stage", [action])
        if action.targeting_tile_action or action.targeting_unit_action:
            self.screen.close_debug_actions()

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
