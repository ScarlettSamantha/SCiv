from typing import TYPE_CHECKING, Any

from direct.task.Task import Task
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.button import Button
from kivy.uix.label import Label

from helpers.cache import Cache
from managers.ui import ui

if TYPE_CHECKING:
    from main import SCIV


class TooltipLabel(Label):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.size_hint = (None, None)  # type: ignore
        # Bind texture_size so the label auto-sizes to content.
        self.bind(texture_size=self._update_size)  # type: ignore

        self.padding = (10, 6)  # type: ignore
        self.color = (1, 1, 1, 1)  # type: ignore # white text

        self.bind(size=self._update_bg, pos=self._update_bg)  # type: ignore

        with self.canvas.before:  # type: ignore
            self.bg_color = Color(0.3, 0.3, 0.3, 0.9)
            self.bg_rect = Rectangle()  # type: ignore

    def _update_size(self, *_):
        # match the label's size to its own texture, plus padding if needed
        self.width, self.height = self.texture_size  # type: ignore

    def _update_bg(self, *_):
        self.bg_rect.pos = self.pos  # type: ignore
        self.bg_rect.size = self.size  # type: ignore


class TooltipBehavior:
    tooltip_text: StringProperty = StringProperty("")
    tooltip_visible: BooleanProperty = BooleanProperty(False)
    tooltip_delay = 0.4  # seconds before tooltip appears

    def __init__(self, **kwargs: Any):
        self.base: "SCIV" = Cache.get_showbase_instance()
        self.base: "SCIV" = Cache.get_showbase_instance()

        self.tooltip_label: TooltipLabel | None = None

        self.base.taskMgr.add(self._poll_mouse_pos, "_poll_mouse_pos")  # type: ignore

        self.register_event_type("on_enter")  # type: ignore
        self.register_event_type("on_leave")  # type: ignore

        self._tooltip_trigger = None

    def _poll_mouse_pos(self, task: Task) -> int:
        if self.base.mouseWatcherNode.hasMouse():  # type: ignore
            win_size = self.base.win.getSize()  # type: ignore
            # Calculate pixel coordinates directly from Panda3D's normalized values.
            px = (self.base.mouseWatcherNode.getMouseX() + 1) * 0.5 * win_size[0]  # type: ignore
            py = (self.base.mouseWatcherNode.getMouseY() + 1) * 0.5 * win_size[1]  # type: ignore
            in_bounds = self.collide_point(*self.to_widget(px, py))  # type: ignore
            if in_bounds:
                self.dispatch("on_enter")  # type: ignore
                if self.tooltip_visible:
                    self.update_tooltip_position(px, py)  # type: ignore
            else:
                self.dispatch("on_leave")  # type: ignore
        return Task.cont

    def update_tooltip_position(self, x: float, y: float):
        if self.tooltip_label:
            parent = ui.get_singleton_instance().get_main_game_ui()
            # Convert window coordinates to the parent's coordinate space.
            local_x, local_y = parent.to_widget(x, y)
            offset = 10  # Offset to avoid covering the cursor.
            self.tooltip_label.x = local_x + offset
            self.tooltip_label.y = local_y + offset

    def on_enter(self, *args: Any):
        if not self.tooltip_visible and self.tooltip_text:
            if self._tooltip_trigger is None:  # type: ignore
                self._tooltip_trigger = Clock.schedule_once(  # type: ignore
                    self.show_tooltip,
                    self.tooltip_delay,
                )

    def on_leave(self, *args: Any):
        if self._tooltip_trigger:  # type: ignore
            self._tooltip_trigger.cancel()  # type: ignore
            self._tooltip_trigger = None
        self.hide_tooltip()

    def show_tooltip(self, dt: Any):
        if not self.tooltip_visible:

            self.tooltip_label = TooltipLabel(text=self.tooltip_text, opacity=0)
            parent = ui.get_singleton_instance().get_main_game_ui()

            if self.tooltip_label in parent.children:
                parent.remove_widget(self.tooltip_label)  # type: ignore
            parent.add_widget(self.tooltip_label)  # type: ignore


            if self.base.mouseWatcherNode.hasMouse():  # type: ignore
                win_size = self.base.win.getSize()  # type: ignore
                px = (self.base.mouseWatcherNode.getMouseX() + 1) * 0.5 * win_size[0]  # type: ignore
                py = (self.base.mouseWatcherNode.getMouseY() + 1) * 0.5 * win_size[1]  # type: ignore
                self.update_tooltip_position(px, py)  # type: ignore

            # Now reveal the tooltip
            self.tooltip_label.opacity = 1
            self.tooltip_visible = True

    def hide_tooltip(self):
        if self.tooltip_label and self.tooltip_visible:
            ui.get_singleton_instance().get_main_game_ui().remove_widget(self.tooltip_label)  # type: ignore
        self.tooltip_label = None
        self.tooltip_visible = False


class TooltippedButton(Button, TooltipBehavior):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)  # type: ignore
