from typing import Optional
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.slider import Slider
from kivy.uix.checkbox import CheckBox
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle

from gameplay.repositories.civilization import Civilization
from menus.kivy.elements.scrollable_popup import ScrollablePopup


class GameConfigMenu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout: Optional[BoxLayout] = None
        self.players: Optional[Slider] = None
        self.players_label: Optional[Label] = None
        self.selected_resolution: Optional[Button] = None
        self.dev_mode: Optional[CheckBox] = None
        self.start: Optional[Button] = None
        self.back: Optional[Button] = None
        self.selected_civilization = "Select Civilization"

        self.add_widget(self.build_screen())

    def build_screen(self):
        float_layout = FloatLayout()
        container: BoxLayout = BoxLayout(
            orientation="vertical",
            size_hint=(0.4, 0.7),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            padding=(10, 30),
            spacing=15,
        )

        with container.canvas.before:
            Color(0.5, 0.5, 0.5, 0.5)
            self.rect = Rectangle(size=container.size, pos=container.pos)

        def update_rect(instance, value):
            self.rect.size = instance.size
            self.rect.pos = instance.pos

        container.bind(size=update_rect, pos=update_rect)

        title_label: Label = Label(
            text="SCIV",
            font_size=40,
            size_hint=(1.0, 1.0),
            height=60,
        )
        container.add_widget(title_label)

        self.players_label = Label(text="Players: 4", size_hint=(1, None), height=30)
        self.players = Slider(min=2, max=12, step=1, value=4, size_hint=(1, None), height=50)

        def update_players_label(instance, value):
            self.players_label.text = f"Players: {int(value)}"

        self.players.bind(value=update_players_label)

        container.add_widget(self.players_label)
        container.add_widget(self.players)

        grid = GridLayout(cols=3, size_hint=(1, None), height=200, spacing=5)
        resolutions = ["720p", "1080p", "1440p", "4K"]
        aspect_ratios = ["16:9", "16:10", "Ultrawide"]

        def select_resolution(button):
            if self.selected_resolution:
                self.selected_resolution.background_color = (1, 1, 1, 1)
            self.selected_resolution = button
            button.background_color = (0, 0, 1, 1)

        for res in resolutions:
            for aspect in aspect_ratios:
                btn = Button(text=f"{res} {aspect}", size_hint=(1, None), height=40)
                btn.bind(on_release=lambda btn: select_resolution(btn))
                grid.add_widget(btn)

        container.add_widget(Label(text="Resolution"))
        container.add_widget(grid)

        # Civilization Selection with Extra Padding Below
        civilization_section = BoxLayout(orientation="vertical", size_hint=(1, None), spacing=10)

        civilization_section.add_widget(Label(text="Civilization"))

        self.dropdown_button = Button(text=self.selected_civilization, size_hint=(1, None), height=50)
        self.dropdown_button.bind(on_release=self.open_civilization_popup)
        civilization_section.add_widget(self.dropdown_button)

        container.add_widget(civilization_section)

        # Adding extra spacing before Back and Start buttons
        container.add_widget(Widget(size_hint_y=None, height=20))  # Adds extra padding

        self.dev_mode = CheckBox()
        container.add_widget(Label(text="Developer Mode"))
        container.add_widget(self.dev_mode)

        self.start = Button(text="Start", size_hint=(1, None), height=50)
        container.add_widget(self.start)

        self.back = Button(text="Back", size_hint=(1, None), height=50)
        container.add_widget(self.back)

        float_layout.add_widget(container)
        return float_layout

    def open_civilization_popup(self, instance):
        kv_values = {}
        for civ in Civilization.all():
            kv_values[str(civ.name)] = civ

        popup = ScrollablePopup("Civilizations", kv_values, self.select_civilization)
        popup.open()

    def select_civilization(self, civilization, value):
        """Updates the civilization selection button"""
        self.selected_civilization = civilization
        print(f"{civilization}, {value}")
        self.dropdown_button.text = civilization
