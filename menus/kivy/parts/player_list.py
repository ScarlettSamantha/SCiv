from typing import TYPE_CHECKING, Any, List, Optional

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from kivy.app import Widget
from kivy.graphics import Color, Rectangle
from kivy.input import MotionEvent
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from panda3d.core import GraphicsWindow, WindowProperties  # type:ignore  # Import GraphicsWindow

from gameplay.player import Player
from helpers.colors import Colors
from main import Cache
from managers.player import PlayerManager

if TYPE_CHECKING:
    from main import SCIV


class PlayerList(FloatLayout, DirectObject):
    def __init__(self, base: "SCIV", **kwargs: Any):
        super().__init__(**kwargs)
        self.base: "SCIV" = base
        self.players: Optional[List[Player]] = None
        self.is_build: bool = False
        self.window: "GraphicsWindow" = self.base.win  # type: ignore
        self.window_properties: WindowProperties = self.window.properties  # type: ignore
        self.background_image = Cache.get_icon_atlas().get_coreimage_by_virtual_path("player_portrait.png")
        # Create internal GridLayout
        self.grid = GridLayout(
            rows=1,
            spacing=-10,
            padding=10,
            size_hint=(0.1, 0.1),
            width=600,
            height=200,
            pos_hint={"top": 0.985, "right": 0.85},
        )
        self.size_hint = (0.5, 0.1)  # type: ignore
        self.pos_hint = {"right": 0.75, "top": 0.985}

        self.add_widget(self.grid)

        # Reposition when window size changes
        self.grid.bind(size=self.update_position)
        self.disabled = True

    def update_position(self, *args: Any):
        text_length = sum(len(str(player.civilization.name)) * 16 for player in self.players)  # type: ignore
        if self.window:
            self.grid.x = self.window_properties.get_x_size() - self.grid.width - (text_length)  # type: ignore
            self.grid.y = self.window_properties.get_y_size() - self.grid.height  # type: ignore

    def build(self) -> None:
        self.players = list(PlayerManager.all().values())

        for player in self.players:
            if player.is_nature or player.is_barbarian:
                continue
            widget = self._generate_player_widget(player)
            self.grid.add_widget(widget)

        self.update_position()
        self.is_build = True

    def _generate_player_widget(self, player: Player) -> FloatLayout:
        container = FloatLayout(
            size_hint=(None, None),
            size=(self.background_image.size[0], self.background_image.size[1]),  # type: ignore
        )

        # Load background texture
        bg_texture = self.background_image.texture  # type: ignore
        with container.canvas.before:  # type: ignore
            Color(1, 1, 1, 1)  # Full white, no tint
            bg_rect = Rectangle(texture=bg_texture, pos=container.pos, size=container.size)  # type: ignore

        # Local function to update background position
        def update_bg(instance: Widget, value: Any):
            bg_rect.pos = instance.pos  # type: ignore
            bg_rect.size = instance.size

        container.bind(pos=update_bg, size=update_bg)

        # Player icon
        icon = Image(
            source=player.icon,
            size_hint=(None, None),
            size=(48, 48),
            pos_hint={"center_x": 0.5, "top": 0.975},
        )

        # Civilization name label
        name = Label(
            text=f"[color={Colors.to_hex(player.color)}]{player.civilization.name}[/color]",
            size_hint=(None, None),
            size=(100, 30),
            pos_hint={"center_x": 0.5, "top": 0.675},
            halign="center",
            valign="middle",
            markup=True,
        )
        name.bind(size=lambda instance, value: setattr(instance, "text_size", value))  # type: ignore

        # Update grid size
        self.grid.width = ((len(self.players) - 2) * (200 + 20)) + 42  # type: ignore
        self.grid.height = 200 + 20

        container.add_widget(icon)
        container.add_widget(name)

        # Add click behavior
        def on_touch_down(instance: Widget, touch: "MotionEvent"):
            if self.disabled:
                return False
            if container.collide_point(*touch.pos):  # type: ignore
                if touch.button == "left":  # type: ignore
                    self._on_player_left_click(player)
                elif touch.button == "right":  # type: ignore
                    self._on_player_right_click(player)
                return True
            return False

        container.bind(on_touch_down=on_touch_down)

        return container

    def _on_player_left_click(self, player: Player) -> None: ...
    def _on_player_right_click(self, player: Player) -> None:
        MessengerGlobal.messenger.send("ui.update.ui.show_player_info", [player])

    def update_bg(self, instance: Widget, value: Any):
        if hasattr(self, "bg_rect"):
            self.bg_rect.pos = instance.pos  # type: ignore
            self.bg_rect.size = instance.size  # type: ignore
