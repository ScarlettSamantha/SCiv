from math import floor
from typing import TYPE_CHECKING, Optional

from direct.showbase.DirectObject import DirectObject
from kivy.graphics import Color, Rectangle
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from exceptions.invalid_pregame_condition import InvalidPregameCondition
from managers.player import PlayerManager
from managers.turn import Turn

if TYPE_CHECKING:
    from gameplay.player import Player
    from main import SCIV


class TopBar(AnchorLayout, DirectObject):
    def __init__(self, base: "SCIV", background_color=(0, 0, 0, 0.9), border=(0, 0, 0, 0), *args, **kwargs):
        self.background_color = background_color
        self.border = border
        self.background_image = None
        super().__init__(*args, **kwargs)
        self.base: "SCIV" = base

        self.frame: Optional[BoxLayout] = None
        self.gold_label: Optional[Label] = None
        self.faith_label: Optional[Label] = None
        self.science_label: Optional[Label] = None
        self.culture_label: Optional[Label] = None
        self.turn_label: Optional[Label] = None

        self.register()

    def register(self):
        self.accept("ui.update.ui.refresh_top_bar", self.update)

    def reset(self):
        self.build()

    def update(self):
        try:
            player: Player = PlayerManager.session_player()
            turn: int = Turn.get_instance().turn
        except InvalidPregameCondition:  # this happens when a game is being loaded
            self.gold_label.text = "Gold: 0"  # type: ignore
            self.faith_label.text = "Faith: 0"  # type: ignore
            self.science_label.text = "Science: 0"  # type: ignore
            self.culture_label.text = "Culture: 0"  # type: ignore
            self.turn_label.text = "Turn: 0"  # type: ignore
            return

        if (
            self.gold_label is None
            or self.faith_label is None
            or self.science_label is None
            or self.culture_label is None
            or self.turn_label is None
        ):
            raise ValueError("Top Bar labels have not been built yet.")

        self.gold_label.text = f"Gold: {str(floor(player.gold.gold.value))}"
        self.faith_label.text = f"Faith: {str(floor(player.faith.faith.value))}"
        self.science_label.text = f"Science: {str(floor(player.science.science.value))}"
        self.culture_label.text = f"Culture: {str(floor(player.culture.culture.value))}"
        self.turn_label.text = f"Turn: {turn}"

    def build(self) -> AnchorLayout:
        # --- Top Bar centered layout ---
        self.anchor_layout = AnchorLayout(
            anchor_x="center", anchor_y="top", size_hint=(1, None), height=30, pos_hint={"top": 1}
        )

        # Single frame for widgets, growing from the center
        self.frame = BoxLayout(orientation="horizontal", size_hint=(None, None), height=30, spacing=10)
        self.frame.bind(children=self.update_frame_width)

        with self.anchor_layout.canvas.before:
            Color(0, 0, 0, 0.8)  # Black background with 50% opacity
            self.rect = Rectangle(size=self.anchor_layout.size, pos=self.anchor_layout.pos)

        def update_camera_rect(instance, value):
            self.rect.size = instance.size  # type: ignore
            self.rect.pos = instance.pos  # type: ignore

        self.anchor_layout.bind(size=update_camera_rect, pos=update_camera_rect)

        self.gold_label = Label(
            text="Gold: 0",
            size_hint=(None, None),
            width=100,
            height=30,
            font_size="15sp",
            valign="middle",
            halign="center",
            text_size=(100, 30),
            color=(1, 1, 1, 1),
            padding=(10, 0),
        )

        self.faith_label = Label(
            text="Faith: 0",
            size_hint=(None, None),
            width=100,
            height=30,
            font_size="15sp",
            valign="middle",
            halign="center",
            text_size=(100, 30),
            color=(1, 1, 1, 1),
            padding=(10, 0),
        )

        self.science_label = Label(
            text="Science: 0",
            size_hint=(None, None),
            width=100,
            height=30,
            font_size="15sp",
            valign="middle",
            halign="center",
            text_size=(100, 30),
            color=(1, 1, 1, 1),
            padding=(10, 0),
        )

        self.culture_label = Label(
            text="Culture: 0",
            size_hint=(None, None),
            width=100,
            height=30,
            font_size="15sp",
            valign="middle",
            halign="center",
            text_size=(100, 30),
            color=(1, 1, 1, 1),
            padding=(10, 0),
        )

        self.turn_label = Label(
            text="Turn: 0",
            size_hint=(None, None),
            width=100,
            height=30,
            font_size="15sp",
            valign="middle",
            halign="center",
            text_size=(100, 30),
            color=(1, 1, 1, 1),
            padding=(10, 0),
        )

        # Center label and other widgets in one frame
        # Order matters here as they will be added in order and be pushed to the right
        self.frame.add_widget(self.turn_label)
        self.frame.add_widget(self.culture_label)
        self.frame.add_widget(self.gold_label)
        self.frame.add_widget(self.science_label)
        self.frame.add_widget(self.faith_label)
        self.anchor_layout.add_widget(self.frame)

        return self.anchor_layout

    def update_frame_width(self, instance, value):
        if self.frame is None:
            return

        total_width = sum(child.width for child in self.frame.children) + (10 * (len(self.frame.children) - 1))
        self.frame.width = total_width

    def get_frame(self) -> BoxLayout:
        if not self.frame:
            raise ValueError("Top Bar frame has not been built yet.")
        return self.frame

    def add_widget_item(self, widget):
        if self.frame is None:
            return

        self.frame.add_widget(widget)
        self.update_frame_width(None, None)
        return widget

    def remove_widget_item(self, widget):
        if self.frame is None:
            return

        if widget in self.frame.children:
            self.frame.remove_widget(widget)
            self.update_frame_width(None, None)
        return widget

    def clear_widgets_items(self) -> BoxLayout | None:
        if self.frame is None:
            return

        self.frame.clear_widgets()
        self.update_frame_width(None, None)
        return self.frame
