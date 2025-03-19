from typing import Optional, Tuple, Type

from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget

from gameplay.civilization import Civilization as BaseCivilization
from gameplay.repositories.civilization import Civilization
from menus.kivy.elements.button_value import ButtonValue
from menus.kivy.elements.scrollable_popup import ScrollablePopup


class GameConfigMenu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout: Optional[FloatLayout] = None
        self.container: Optional[BoxLayout] = None
        self.civilization_section: Optional[BoxLayout] = None

        self.title_label: Optional[Label] = None
        self.civ_popup: Optional[Popup] = None

        self.players: Optional[Slider] = None
        self.players_label: Optional[Label] = None
        self.dev_mode: Optional[CheckBox] = None
        self.start: Optional[Button | Widget] = None
        self.back: Optional[Button | Widget] = None
        self.size_section: Optional[BoxLayout] = None
        self.size_popup: Optional[ScrollablePopup] = None
        self.size_popup_button: Optional[Button] = None

        self.selected_size: Optional[Tuple[int, int]] = None
        self.selected_civilization: Optional[Type[BaseCivilization]] = None
        self.player_count: int = 4

        self.add_widget(self.build_screen())

    def build_screen(self):
        self.layout = FloatLayout()
        self.container = BoxLayout(
            orientation="vertical",
            size_hint=(0.4, 0.8),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            padding=(10, 10),
            spacing=0,
        )

        with self.container.canvas.before:  # type: ignore
            Color(0.5, 0.5, 0.5, 0.5)
            self.rect = Rectangle(size=self.container.size, pos=self.container.pos)

        def update_rect(instance, value):
            self.rect.size = instance.size
            self.rect.pos = instance.pos

        self.container.bind(size=update_rect, pos=update_rect)  # type: ignore

        self.title_label = Label(
            text="SCIV - Game Configuration",
            font_size=40,
            size_hint=(1.0, 1.0),
            height=40,
        )
        self.container.add_widget(self.title_label)

        self.players_label = Label(text="Players: 4", size_hint=(1, None), height=30)
        self.players = Slider(min=2, max=12, step=1, value=4, size_hint=(1, None), height=50)

        def update_players_label(instance, value):
            self.players_label.text = f"Players: {int(value)}"  # type: ignore
            self.player_count = int(value)

        self.players.bind(value=update_players_label)  # type: ignore

        self.container.add_widget(self.players_label)
        self.container.add_widget(self.players)

        # Civilization Selection with Extra Padding Below
        self.civilization_section = BoxLayout(orientation="vertical", size_hint=(1, None), spacing=5, padding=(0, 0.2))

        self.civilization_section.add_widget(Label(text="Civilization"))

        self.dropdown_button = Button(text="Random", size_hint=(1, None), height=50)
        self.dropdown_button.bind(on_release=self.open_civilization_popup)  # type: ignore
        self.civilization_section.add_widget(self.dropdown_button)

        self.container.add_widget(self.civilization_section)

        self.size_section = BoxLayout(orientation="vertical", size_hint=(1, None), spacing=5, padding=(0, 0.2))
        self.size_section.add_widget(Label(text="Map Size"))

        self.size_popup_button = ButtonValue(text="25x25", value=(25, 25), size_hint=(1, None), height=50)
        self.size_popup_button.bind(on_release=self.open_size_popup)  # type: ignore
        self.size_section.add_widget(self.size_popup_button)

        self.container.add_widget(self.size_section)

        # Adding extra spacing before Back and Start buttons
        self.container.add_widget(Widget(size_hint_y=None, height=20))  # Adds extra padding

        self.dev_mode = CheckBox(size_hint=(1, None), height=50)
        self.container.add_widget(Label(text="Developer Mode"))
        self.container.add_widget(self.dev_mode)

        self.button_container = BoxLayout(size_hint=(1, None), height=50, orientation="horizontal", spacing=10)

        self.back = Button(text="Back", size_hint=(None, None), height=50, width=200)
        self.back.on_press = self.back_to_main_menu
        self.button_container.add_widget(self.back)

        # Spacer Widget to push "Start" to the right
        self.button_container.add_widget(Widget(size_hint_x=1))

        self.start = Button(text="Start", size_hint=(None, None), height=50, width=200)
        self.start.on_press = self.start_game
        self.button_container.add_widget(self.start)

        self.container.add_widget(self.button_container)
        self.layout.add_widget(self.container)
        return self.layout

    def open_size_popup(self, instance):
        if self.size_popup is None:
            self.size_popup = ScrollablePopup(
                "Map sizes",
                on_select=self.select_size,
                items={
                    "25x25 (UI test)": (25, 25),
                    "50x50 (Small)": (50, 50),
                    "50x90 (Small 16:9)": (50, 90),
                    "75x120 (Small 4:3)": (75, 120),
                    "90x150 (Medium 3:5)": (90, 150),
                    "100x100 (Medium)": (100, 100),
                    "120x180 (Large 4:3)": (120, 180),
                    "150x150 (Large)": (150, 150),
                    "200x200 (Dont use)": (200, 200),
                },
            )
        self.size_popup.open()

    def open_civilization_popup(self, instance):
        if self.civ_popup is None:
            kv_values = {}
            for civ in Civilization.all():
                kv_values[str(civ.name)] = civ
            self.civ_popup = ScrollablePopup("Civilizations", kv_values, self.select_civilization)
        self.civ_popup.open()

    def select_size(self, size, _value):
        """Updates the resolution selection button"""
        self.selected_size = _value
        self.size_popup_button.text = size  # type: ignore

    def select_civilization(self, civilization, _value: Type[BaseCivilization]):
        """Updates the civilization selection button"""
        self.selected_civilization = _value
        print(f"{civilization}, {_value}")
        self.dropdown_button.text = civilization

    def update_selected_size(self):
        if self.size_popup_button is None:
            raise AssertionError("Size popup button is not initialized")

        size = self.size_popup_button.text.split(" ")[0].split("x")
        self.selected_size = (int(size[0]), int(size[1]))

    def start_game(self):
        from direct.showbase.MessengerGlobal import messenger

        if self.selected_size is None:
            self.update_selected_size()  # To ensure the size is up to date

        size: Tuple[int, int] = self.selected_size  # type: ignore

        if self.selected_civilization is None:
            civ: Type[BaseCivilization] = Civilization.random(1)  # type: ignore
        else:
            civ: Type[BaseCivilization] = self.selected_civilization

        players: int = int(self.player_count)

        messenger.send("system.game.start_load", [size, civ, players])
        self.manager.current = "game_ui"

    def back_to_main_menu(self):
        self.manager.current = "main_menu"
