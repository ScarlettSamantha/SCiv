from typing import Any, List, Optional, Tuple

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from gameplay.ai.goal import Goals
from gameplay.ai.memory import Memories
from gameplay.player import Player
from kivy.graphics import Color, RoundedRectangle  # type: ignore
from kivy.metrics import dp  # type: ignore
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView


class PlayerInfo(FloatLayout, DirectObject):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        DirectObject.__init__(self, **kwargs)

        self.player: Optional[Player] = None
        self._is_build = False

        self.size_hint = (0.9, 0.9)
        self.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        with self.canvas.before:  # type: ignore
            Color(0, 0, 0, 0.7)
            self._overlay = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])  # type: ignore
        self.bind(pos=self._upd_overlay, size=self._upd_overlay)  # type: ignore

        self.opacity = 0
        self.disabled = True
        self.is_open: bool = False

        self.register()

    def _upd_overlay(self, *_) -> None:
        self._overlay.pos = self.pos  # type: ignore
        self._overlay.size = self.size  # type: ignore

    def register(self) -> None:
        self.accept("ui.update.ui.show_player_info", self.show_popup)
        self.accept("ui.update.ui.hide_player_info", self.hide_popup)  # type: ignore

    def set_player(self, player: Player) -> None:
        self.player = player

    def build(self) -> None:
        if self._is_build:
            return
        self.clear_widgets()

        self.top_bar = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(40),
            pos_hint={"top": 1, "right": 1},
            padding=(dp(10), dp(5), dp(5), dp(5)),
        )
        with self.top_bar.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            self._bar_bg = RoundedRectangle(pos=self.top_bar.pos, size=self.top_bar.size, radius=[10, 10, 0, 0])  # type: ignore
        self.top_bar.bind(
            pos=lambda w, *_: setattr(self._bar_bg, "pos", w.pos),  # type: ignore
            size=lambda w, *_: setattr(self._bar_bg, "size", w.size),  # type: ignore
        )

        title = Label(text="Player Info", halign="left", valign="middle")
        title.bind(size=lambda i, v: setattr(i, "text_size", (i.width, i.height)))  # type: ignore
        close_btn = Button(text="✕", size_hint=(None, 1), width=dp(40))  # type: ignore
        close_btn.bind(on_release=lambda *_: self.hide_popup())  # type: ignore

        self.top_bar.add_widget(title)
        self.top_bar.add_widget(close_btn)
        self.add_widget(self.top_bar)

        self.left_panel = BoxLayout(
            orientation="vertical",
            size_hint=(0.45, 0.85),
            pos_hint={"x": 0.05, "y": 0.05},
            spacing=10,
        )
        self.top_right = BoxLayout(
            orientation="vertical",
            size_hint=(0.45, 0.4),
            pos_hint={"x": 0.5, "y": 0.55},
        )
        self.bottom_right = BoxLayout(
            orientation="vertical",
            size_hint=(0.45, 0.4),
            pos_hint={"x": 0.5, "y": 0.05},
        )

        self.add_widget(self.left_panel)
        self.add_widget(self.top_right)
        self.add_widget(self.bottom_right)

        self._is_build = True
        self.disabled = True
        self.opacity = 0
        self.refresh()

    def _row(self, title: str, value: Any) -> BoxLayout:
        w = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(30))
        a = Label(text=title, size_hint=(0.3, 1), halign="left", valign="middle")
        b = Label(text=str(value), size_hint=(0.7, 1), halign="left", valign="middle")

        for lbl in (a, b):
            lbl.bind(size=lambda inst, val: setattr(inst, "text_size", (inst.width, inst.height)))  # type: ignore

        w.add_widget(a)
        w.add_widget(b)
        return w

    def _populate_list_panel(self, panel: BoxLayout, items: List[str | Tuple[str, Any | str]]) -> None:
        panel.clear_widgets()
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        container = BoxLayout(orientation="vertical", size_hint=(1, None), spacing=5)
        container.bind(minimum_height=container.setter("height"))  # type: ignore

        for t, v in items:
            container.add_widget(self._row(t, v))

        scroll.add_widget(container)  # type: ignore
        panel.add_widget(scroll)

    def refresh(self) -> None:
        if not self._is_build or not self.player:
            return

        left_items: List[str | Tuple[str, Any | str]] = [
            ("Name:", self.player.civilization.name),
            ("Player ID:", self.player.id),
            ("Intro:", self.player.introduction),
            ("Color:", self.player.color),
            ("Civilization:", str(self.player.civilization.name)),
            ("Leader:", str(self.player.leader.name)),
            ("Personality:", str(self.player.get_ai().personality)),
            ("Techs:", str(len(self.player.tech))),
            ("Civics:", str(len(self.player.civics))),
            ("Units:", str(len(self.player.units))),
            ("Cities:", str(len(self.player.cities))),
            ("Vision - Tiles:", str(len(self.player.vision.get_visible_tiles()))),
            ("Vision - Units:", str(len(self.player.vision.get_visible_units()))),
            ("Is AI:", not self.player.is_human),
            ("Is Human:", self.player.is_human),
            ("Is Nature:", self.player.is_nature),
            ("Is Barbarian", self.player.is_barbarian),
        ]
        self._populate_list_panel(self.left_panel, left_items)

        memories: Memories = self.player.get_ai().get_memories()
        memories_list: List[str] = [f"Memory: {str(memory)}" for memory in memories]

        goals: Goals = self.player.get_ai().get_goals()
        goals_list: List[str] = [f"Goal: {str(goal)}" for goal in goals]

        top_items: List[str | Tuple[str, Any | str]] = (
            [
                ("Wins:", getattr(self.player, "wins", "N/A")),
                ("Losses:", getattr(self.player, "losses", "N/A")),
            ]
            + memories_list
            + goals_list
        )
        self._populate_list_panel(self.top_right, top_items)  # type: ignore

        bottom_items: List[str | Tuple[str, Any | str]] = [
            ("Score:", getattr(self.player, "score", "N/A")),
            ("Rank:", getattr(self.player, "rank", "N/A")),
        ]
        self._populate_list_panel(self.bottom_right, bottom_items)

    def show_popup(self, player: Player) -> None:
        self.set_player(player)
        if not self._is_build:
            self.build()
        else:
            self.refresh()

        self.opacity = 1
        self.disabled = False
        self.accept_once("escape", self.hide_popup)  # type: ignore

        for msg in (
            "system.input.raycaster_off",
            "system.input.disable_zoom",
            "system.input.disable_control",
            "system.input.camera_lock",
        ):
            MessengerGlobal.messenger.send(msg)

        self.is_open = True

    def hide_popup(self, *_) -> None:
        self.clear_widgets()
        self.opacity = 0
        self.disabled = True
        self._is_build = False

        for msg in (
            "system.input.camera_unlock",
            "system.input.raycaster_on",
            "system.input.enable_zoom",
            "system.input.enable_control",
        ):
            MessengerGlobal.messenger.send(msg)

        self.is_open = False
