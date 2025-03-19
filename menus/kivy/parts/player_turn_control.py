from typing import Optional

from direct.showbase.MessengerGlobal import messenger
from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout

from managers.i18n import t_


class PlayerTurnControl(FloatLayout):
    def __init__(self, base, **kwargs):
        super().__init__(**kwargs)
        self.base = base

        self.frame: Optional[FloatLayout] = None
        self.button: Optional[Button] = None
        self.rect = None

        self.register()

    def register(self):
        self.base.accept("game.turn.start_process", self.on_turn_change_start)
        self.base.accept("ui.update.ui.refresh_player_turn_control", self.on_turn_change_end)

    def get_frame(self) -> FloatLayout:
        if self.frame is None:
            self.frame = self.build_debug_frame()
        return self.frame

    def build_debug_frame(self) -> FloatLayout:
        # --- Player Turn Control (Bottom-Right Corner) ---
        self.frame = FloatLayout(
            size_hint=(None, None),
            width=200,
            height=100,
            pos_hint={"right": 1, "y": 0},
        )

        with self.frame.canvas.before:  # type: ignore
            Color(0, 0, 0, 0.7)  # Black background with 70% opacity
            self.rect = Rectangle(size=self.frame.size, pos=self.frame.pos)

        def update_debug_rect(instance, value):
            self.rect.size = instance.size  # type: ignore
            self.rect.pos = instance.pos  # type: ignore

        self.frame.bind(size=update_debug_rect, pos=update_debug_rect)  # type: ignore

        self.button = Button(
            text="End Turn",
            size_hint=(None, None),
            width=180,
            height=80,
            font_size="14sp",
            valign="center",
            halign="center",
            text_size=(180, 80),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            color=(1, 1, 1, 1),
        )
        self.button.bind(on_press=self.send_end_turn)

        self.frame.add_widget(self.button)
        return self.frame

    def send_end_turn(self, instance):
        messenger.send("game.turn.request_end")

    def on_turn_change_start(self, turn: int):
        if self.button is None:
            raise AssertionError("Button is not set")

        self.button.text = str(t_("ui.player_ui.turn_button.on_turn", {"turn": str(turn)}))

    def on_turn_change_end(self, turn: int):
        if self.button is None:
            raise AssertionError("Button is not set")

        self.button.text = str(t_("ui.player_ui.turn_button.end_turn", {"turn": str(turn)}))
