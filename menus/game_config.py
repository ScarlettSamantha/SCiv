from panda3d_kivy.app import App
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, ListProperty
from direct.showbase.MessengerGlobal import messenger
from gameplay.repositories.civilization import Civilization

KV = r"""
FloatLayout:
    canvas.before:
        Color:
            rgb: (0.5, 0.5, 0.5)  # Gray background
        Rectangle:
            pos: (600, 0)
            size: (1000, 12000)

    BoxLayout:
        orientation: 'vertical'
        size_hint: (0.5, 0.5)  # Adjustable based on window size
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}
        padding: (400, 10)
        spacing: 10
        
        Label:
            text: "Select Map Size:"
        Spinner:
            id: size_spinner
            text: app.map_size
            values: ['50x75', '50x50', '60x120', '90x110', '100x100', '150x150']
            on_text: app.map_size = self.text

        Label:
            text: "Select Civilization:"
        Spinner:
            id: civ_spinner
            text: app.civilization
            values: app.all_civilizations
            on_text: app.civilization = self.text

        Label:
            text: "Number of Players: " + str(app.num_players)
        Slider:
            id: players_slider
            min: 2
            max: 10
            step: 1
            value: app.num_players
            on_value: app.num_players = int(self.value)
            
        Button:
            text: "Start Game"
            color: (0, 1, 0, 1)
            on_press: app.get_game_ui()
"""


class CivSelectorApp(App):
    map_size = StringProperty("50x75")
    civilization = StringProperty("Rome")
    num_players = NumericProperty(4)
    all_civilizations = ListProperty([])
    all_civilizations = ListProperty([str(civ.name).lower() for civ in Civilization.all()])

    def build(self):
        # Build the Kivy UI from the KV string.
        return Builder.load_string(KV)

    def get_game_ui(self):
        messenger.send("system.game.start", [self.map_size, self.civilization, self.num_players])
        self.root.clear_widgets()
        self.window.clear()  # type: ignore
        self.window.remove_widget(self.root)  # type: ignore
        self.stop()
        self._stop()
