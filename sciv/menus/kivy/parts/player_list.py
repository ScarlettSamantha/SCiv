from typing import TYPE_CHECKING, Any, List, Optional, Tuple

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from gameplay.player import Player
from helpers.cache import Cache
from helpers.colors import Colors
from kivy.graphics import Color, Rectangle
from kivy.input import MotionEvent  #  type:ignore
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from managers.player import PlayerManager
from panda3d.core import GraphicsWindow, WindowProperties  # type:ignore  # Import GraphicsWindow

if TYPE_CHECKING:
    from game import OpenCiv


class PlayerList(FloatLayout, DirectObject):
    def __init__(self, base: "OpenCiv", **kwargs: Any):
        super().__init__(**kwargs)
        self.base: "OpenCiv" = base
        self.players: Optional[List[Player]] = None
        self.is_build: bool = False
        self.window: "GraphicsWindow" = self.base.win  # type: ignore
        self.window_properties: WindowProperties = self.window.properties  # type: ignore
        self.background_image = Cache.get_icon_atlas().get_coreimage_by_virtual_path("player_portrait.png")
        self.size_hint_x = None
        self.size_hint_y = 0.1

        self.grid = GridLayout(
            rows=1,
            spacing=-10,
            padding=10,
            size_hint=(None, None),
            width=300,
            height=200,
            pos_hint={"top": 0.985, "right": 1},
        )
        self.pos_hint = {"right": 0.80, "top": 0.985}

        self.add_widget(self.grid)

        self.grid.bind(size=self.update_position)
        self.disabled = True

    def update_position(self, *args: Any):
        if not self.players or not self.grid.children:
            return

        children: List[Widget] = list(self.grid.children)
        total_w = sum(w.width for w in children)
        h_spacing = self.grid.spacing[0] if isinstance(self.grid.spacing, (tuple, list)) else self.grid.spacing
        total_w += h_spacing * (len(children) - 1)

        pad: Tuple[int, ...] | List[int] | int = self.grid.padding
        if isinstance(pad, (tuple, list)) and len(pad) == 4:
            left, top, right, _ = pad
        elif isinstance(pad, int):
            left = top = right = _ = pad
        else:
            raise ValueError("Padding must be a tuple of 4 integers or a single integer.")

        total_w: int = total_w + left + right

        total_h: int = self.grid.height

        self.grid.width = total_w
        self.grid.height = total_h

        win_h: int = self.window_properties.get_y_size()
        self.grid.x = right - self.grid.width
        self.grid.y = win_h - top - self.grid.height

        self.width = self.grid.width
        self.height = self.grid.height

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

        bg_texture = self.background_image.texture  # type: ignore
        with container.canvas.before:  # type: ignore
            Color(1, 1, 1, 1)  # Full white, no tint
            bg_rect = Rectangle(texture=bg_texture, pos=(0, 0), size=container.size)  # type: ignore

        def update_bg(instance: Widget, value: Any):
            bg_rect.pos = instance.pos  # type: ignore
            bg_rect.size = instance.size

        container.bind(pos=update_bg, size=update_bg)

        icon = Image(
            source=player.icon,
            size_hint=(None, None),
            size=(48, 48),
            pos_hint={"center_x": 0.5, "top": 0.975},
        )

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

        self.grid.width = (len(self.players) - 2) * (100 + 20)  # type: ignore
        self.grid.height = 200 + 20
        self.width = self.grid.width
        self.height = self.grid.height

        container.add_widget(icon)
        container.add_widget(name)

        def on_touch_down(instance: Widget, touch: MotionEvent):  # type: ignore
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

    def _on_player_left_click(self, player: Player) -> None:
        self.base.ui_manager.get_main_game_ui().inspect_element(player)

    def _on_player_right_click(self, player: Player) -> None:
        MessengerGlobal.messenger.send("ui.update.ui.show_player_info", [player])

    def update_bg(self, instance: Widget, value: Any):
        if hasattr(self, "bg_rect"):
            self.bg_rect.pos = instance.pos  # type: ignore
            self.bg_rect.size = instance.size  # type: ignore
