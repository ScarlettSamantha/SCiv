from typing import Optional

from direct.showbase.MessengerGlobal import messenger
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen


class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout: Optional[FloatLayout] = None
        self.container: Optional[BoxLayout] = None

        self.continue_button: Optional[Button] = None
        self.new_button: Optional[Button] = None
        self.load_button: Optional[Button] = None
        self.options_button: Optional[Button] = None
        self.credit_button: Optional[Button] = None
        self.code_button: Optional[Button] = None
        self.exit_button: Optional[Button] = None

        self.add_widget(self.build_screen())

    def switch_to_game_config_screen(self, _):
        self.manager.current = "game_config_screen"

    def build_screen(self):
        float_layout = FloatLayout()
        self.layout = float_layout
        # Transparent gray background box
        container: BoxLayout = BoxLayout(
            orientation="vertical",
            size_hint=(0.4, 0.7),  # Taller than it is wide
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            padding=(10, 20),
            spacing=15,
        )

        with container.canvas.before:  # type: ignore # noqa
            Color(0.5, 0.5, 0.5, 0.5)  # Gray with transparency
            self.rect = Rectangle(size=container.size, pos=container.pos)

        def update_rect(instance, value):
            self.rect.size = instance.size
            self.rect.pos = instance.pos

        container.bind(size=update_rect, pos=update_rect)  # type: ignore

        # Title label
        title_label: Label = Label(
            text="SCIV",
            font_size=40,
            size_hint=(1.0, 1.0),
            height=60,
        )
        container.add_widget(title_label)

        self.container = container

        button_width: int = 400

        self.continue_button = Button(text="Continue", size_hint=(None, None), height=50, width=button_width)
        self.continue_button.pos_hint = {"center_x": 0.5}

        self.new_button = Button(text="New", size_hint=(None, None), height=50, width=button_width)
        self.new_button.pos_hint = {"center_x": 0.5}
        self.new_button.bind(on_release=self.switch_to_game_config_screen)

        self.load_button = Button(text="Load", size_hint=(None, None), height=50, width=button_width)
        self.load_button.pos_hint = {"center_x": 0.5}
        self.load_button.bind(on_release=self.switch_to_load_screen)

        self.options_button = Button(text="Options", size_hint=(None, None), height=50, width=button_width)
        self.options_button.pos_hint = {"center_x": 0.5}
        self.options_button.on_press = self.to_config_screen

        self.credit_button = Button(text="Credits", size_hint=(None, None), height=50, width=button_width)
        self.credit_button.pos_hint = {"center_x": 0.5}

        self.code_button = Button(text="Code", size_hint=(None, None), height=50, width=button_width)
        self.code_button.pos_hint = {"center_x": 0.5}

        self.exit_button = Button(text="Exit", size_hint=(None, None), height=50, width=button_width)
        self.exit_button.pos_hint = {"center_x": 0.5}
        self.exit_button.bind(on_press=exit)

        container.add_widget(self.continue_button)
        container.add_widget(self.new_button)
        container.add_widget(self.load_button)
        container.add_widget(self.options_button)
        container.add_widget(self.credit_button)
        container.add_widget(self.code_button)
        container.add_widget(self.exit_button)

        float_layout.add_widget(container)
        return float_layout

    def to_config_screen(self, _):
        self.manager.current = "options_screen"

    def switch_to_load_screen(self, _):
        messenger.send("ui.update.ui.show_load")

    def switch_to_save_screen(self, _):
        messenger.send("ui.update.ui.show_save")

    def exit(self):
        messenger.send("game.input.user.quit_game")
