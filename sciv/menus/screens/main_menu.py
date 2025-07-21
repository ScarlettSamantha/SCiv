from typing import Any, Optional

from direct.showbase.MessengerGlobal import messenger
from helpers.colors import Colors
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.widget import Widget
from menus.kivy.elements.clickable_label import ClickableLabel

from sciv.gameplay.repositories.civilization import Civilization


class MainMenuScreen(Screen):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.layout: Optional[FloatLayout] = None
        self.container: Optional[BoxLayout] = None
        self.manager: ScreenManager
        self.quick_start_button: Optional[Button] = None
        self.continue_button: Optional[Button] = None
        self.new_button: Optional[Button] = None
        self.load_button: Optional[Button] = None
        self.options_button: Optional[Button] = None
        self.credit_button: Optional[Button] = None
        self.code_button: Optional[Button] = None
        self.exit_button: Optional[Button] = None

        self.add_widget(self.build_screen())

    def switch_to_game_config_screen(self, _: Any):
        self.manager.current = "game_config_screen"

    def build_screen(self):
        from helpers.debug import Debug

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
            self.rect = Rectangle(size=container.size, pos=container.pos)  # type: ignore

        def update_rect(instance: Widget, value: Any):
            self.rect.size = instance.size  # type: ignore
            self.rect.pos = instance.pos  # type: ignore

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

        if Debug.is_debug():
            self.quick_start_button = Button(
                text="Quick Start",
                size_hint=(None, None),
                height=50,
                width=button_width,
            )
            self.quick_start_button.pos_hint = {"center_x": 0.5}
            self.quick_start_button.bind(on_release=self.quick_start)
            container.add_widget(self.quick_start_button)

        self.continue_button = Button(text="Continue", size_hint=(None, None), height=50, width=button_width)
        self.continue_button.pos_hint = {"center_x": 0.5}
        self.continue_button.disabled = True
        self.continue_button.bind(on_release=self.hide)

        self.new_button = Button(text="New", size_hint=(None, None), height=50, width=button_width)
        self.new_button.pos_hint = {"center_x": 0.5}
        self.new_button.bind(on_release=self.switch_to_game_config_screen)

        self.load_button = Button(text="Load", size_hint=(None, None), height=50, width=button_width)
        self.load_button.pos_hint = {"center_x": 0.5}
        self.load_button.bind(on_release=self.switch_to_load_screen)

        self.options_button = Button(text="Options", size_hint=(None, None), height=50, width=button_width)
        self.options_button.pos_hint = {"center_x": 0.5}
        self.options_button.bind(on_release=self.to_config_screen)

        self.credit_button = Button(text="Credits", size_hint=(None, None), height=50, width=button_width)
        self.credit_button.disabled = True
        self.credit_button.pos_hint = {"center_x": 0.5}

        self.code_button = Button(text="Code", size_hint=(None, None), height=50, width=button_width)
        self.code_button.bind(on_release=self.open_browser_to_code)
        self.code_button.pos_hint = {"center_x": 0.5}

        self.exit_button = Button(text="Exit", size_hint=(None, None), height=50, width=button_width)
        self.exit_button.pos_hint = {"center_x": 0.5}
        self.exit_button.bind(on_press=self.exit)

        container.add_widget(self.continue_button)
        container.add_widget(self.new_button)
        container.add_widget(self.load_button)
        container.add_widget(self.options_button)
        container.add_widget(self.credit_button)
        container.add_widget(self.code_button)
        container.add_widget(self.exit_button)

        float_layout.add_widget(container)

        footer: BoxLayout = BoxLayout(
            orientation="horizontal",
            size_hint=(1.0, None),
            height=50,
            pos_hint={"center_x": 0.5, "center_y": 0.01},
        )

        dev_color = Colors.to_hex(Colors.RED)
        path_color = Colors.to_hex(Colors.GREEN)
        _commit = f"[color={dev_color}]{Debug.get_git_commit()[:8]}[{Debug.get_git_branch()}][/color]"
        _config_file = f"[color={path_color}]{Debug.get_config_path()}[/color]"

        version_text = f"Git Commit: {_commit} | Panda3D: {Debug.get_panda_version()} | Kivy: {Debug.get_kivy_version()} | Config: {_config_file}"
        version_label: Label = ClickableLabel(
            text=version_text,
            size_hint=(0.02, 1.0),
            font_size=20,
            halign="center",
            valign="middle",
            markup=True,
            on_click=self._on_label_click,
        )
        footer.add_widget(version_label)
        float_layout.add_widget(footer)
        return float_layout

    def quick_start(self, _: Optional[Button] = None):
        messenger.send("system.game.start_load", [(25, 25), Civilization.random(num=1), 3])

    def _on_label_click(self, *args: Any, **kwargs: Any) -> None:
        from helpers.debug import Debug

        Debug.open_config_folder()
        Debug.open_data_folder()

    def to_config_screen(self, _: Any):
        self.manager.current = "options_screen"

    def to_game_screen(self, _: Optional[Button] = None):
        self.manager.current = "game_ui"
        messenger.send("system.input.raycaster_on")

    def switch_to_load_screen(self, _: Any):
        messenger.send("ui.update.ui.show_load")

    def switch_to_save_screen(self, _: Any):
        messenger.send("ui.update.ui.show_save")

    def open_browser_to_code(self, _: Optional[Button] = None):
        import webbrowser

        from system.vars import REPOSITORY

        webbrowser.open_new_tab(REPOSITORY)

    def exit(self, _: Optional[Button] = None):
        messenger.send("game.input.user.quit_game")

    def hide(self, _: Optional[Button] = None):
        self.layout.visible = False  # type: ignore
        self.to_game_screen()

    def show(self):
        self.layout.visible = True  # type: ignore
