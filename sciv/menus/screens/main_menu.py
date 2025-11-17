from typing import Any, Optional

from direct.showbase import MessengerGlobal
from direct.showbase.MessengerGlobal import messenger
from gameplay.repositories.civilization import Civilization
from helpers.colors import Colors
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.widget import Widget
from managers.i18n import Translation
from menus.kivy.elements.clickable_label import ClickableLabel
from menus.kivy.elements.menu_styled import DarkPanel, PrimaryButton  # type: ignore


class MainMenuScreen(Screen):
    def __init__(self, **kwargs: Any) -> None:
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
        self._background_rect: Optional[Rectangle] = None

        self.add_widget(self.build_screen())

    def switch_to_game_config_screen(self, _: Any) -> None:
        self.manager.current = "game_config_screen"

    def build_screen(self) -> FloatLayout:
        from helpers.debug import Debug

        float_layout = FloatLayout()
        self.layout = float_layout

        with float_layout.canvas.before:  # type: ignore
            Color(0.02, 0.02, 0.04, 1.0)
            self._background_rect = Rectangle(size=float_layout.size, pos=float_layout.pos)  # type: ignore

        def update_background(instance: Widget, _: Any) -> None:
            if self._background_rect is not None:
                self._background_rect.size = instance.size
                self._background_rect.pos = instance.pos

        float_layout.bind(size=update_background, pos=update_background)  # type: ignore

        container = DarkPanel(
            orientation="vertical",
            size_hint=(0.4, 0.7),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            padding=(dp(32), dp(28)),
            spacing=dp(16),
        )

        header = BoxLayout(
            orientation="vertical",
            size_hint=(1.0, None),
            height=dp(120),
            padding=(0, 0, 0, dp(8)),
            spacing=dp(4),
        )

        title_label = Label(
            text="[b]%s[/b]" % str(Translation("ui.player_ui.main_menu.title")),
            font_size="42sp",
            size_hint=(1.0, None),
            height=dp(54),
            markup=True,
            halign="center",
            valign="middle",
        )

        subtitle_label = Label(
            text=str(Translation("ui.player_ui.main_menu.under_title")),
            font_size="18sp",
            size_hint=(1.0, None),
            height=dp(32),
            color=(0.75, 0.75, 0.8, 1.0),
            halign="center",
            valign="middle",
        )

        def _update_header_label(instance: Label, _: Any) -> None:
            instance.text_size = instance.size  # type: ignore

        title_label.bind(size=_update_header_label)  # type: ignore
        subtitle_label.bind(size=_update_header_label)  # type: ignore

        header.add_widget(title_label)
        header.add_widget(subtitle_label)
        container.add_widget(header)

        self.container = container

        button_width = dp(400)

        def create_menu_button(text: str) -> Button:
            button = PrimaryButton(
                text=text,
                size_hint=(1.0, None),
                height=dp(48),
                width=button_width,
                font_size="20sp",
            )
            button.pos_hint = {"center_x": 0.5}
            return button

        if Debug.is_debug():
            self.quick_start_button = create_menu_button(str(Translation("ui.player_ui.main_menu.quick_start")))
            self.quick_start_button.background_color = (0.32, 0.24, 0.12, 1.0)
            self.quick_start_button.bind(on_release=self.quick_start)
            container.add_widget(self.quick_start_button)

        self.continue_button = create_menu_button(str(Translation("ui.player_ui.main_menu.continue")))
        self.continue_button.disabled = True
        self.continue_button.bind(on_release=self.hide)

        self.new_button = create_menu_button(str(Translation("ui.player_ui.main_menu.new_game")))
        self.new_button.bind(on_release=self.switch_to_game_config_screen)

        self.load_button = create_menu_button(str(Translation("ui.player_ui.main_menu.load_game")))
        self.load_button.bind(on_release=self.switch_to_load_screen)

        self.options_button = create_menu_button(str(Translation("ui.player_ui.main_menu.options")))
        self.options_button.bind(on_release=self.to_config_screen)

        self.credit_button = create_menu_button(str(Translation("ui.player_ui.main_menu.credits")))
        self.credit_button.disabled = True

        self.code_button = create_menu_button(str(Translation("ui.player_ui.main_menu.view_source")))
        self.code_button.bind(on_release=self.open_browser_to_code)

        self.exit_button = create_menu_button(str(Translation("ui.player_ui.main_menu.quit")))
        self.exit_button.bind(on_press=self.exit)

        container.add_widget(self.continue_button)
        container.add_widget(self.new_button)
        container.add_widget(self.load_button)
        container.add_widget(self.options_button)
        container.add_widget(self.credit_button)
        container.add_widget(self.code_button)
        container.add_widget(self.exit_button)

        float_layout.add_widget(container)

        footer = BoxLayout(
            orientation="horizontal",
            size_hint=(1.0, None),
            height=dp(32),
            padding=(dp(12), 0, dp(12), dp(8)),
            pos_hint={"x": 0.0, "y": 0.0},
        )

        dev_color = Colors.to_hex(Colors.RED)
        path_color = Colors.to_hex(Colors.GREEN)

        commit = Debug.get_git_commit()
        branch = Debug.get_git_branch()
        commit_str = f"{commit[:8]}[{branch}]" if commit and branch else commit[:8]
        commit_markup = f"[color={dev_color}]{commit_str}[/color]"

        config_path = Debug.get_config_path()
        config_markup = f"[color={path_color}]{config_path}[/color]"

        version_text = (
            f"Build {commit_markup} • "
            f"Panda3D {Debug.get_panda_version()} • "
            f"Kivy {Debug.get_kivy_version()} • "
            f"Config {config_markup}"
        )

        version_label = ClickableLabel(
            text=version_text,
            size_hint=(1.0, 1.0),
            font_size="14sp",
            halign="center",
            valign="middle",
            markup=True,
            on_click=self._on_label_click,
        )

        def _update_version_label(instance: Label, _: Any) -> None:
            instance.text_size = instance.size  # type: ignore

        version_label.bind(size=_update_version_label)  # type: ignore

        footer.add_widget(version_label)
        float_layout.add_widget(footer)

        return float_layout

    def quick_start(self, _: Optional[Button] = None) -> None:
        MessengerGlobal.messenger.send("system.game.start_load", [(25, 25), Civilization.random(num=1), 3])

    def _on_label_click(self, *args: Any, **kwargs: Any) -> None:
        from helpers.debug import Debug

        Debug.open_config_folder()
        Debug.open_data_folder()

    def to_config_screen(self, _: Any) -> None:
        self.manager.current = "options_screen"

    def to_game_screen(self, _: Optional[Button] = None) -> None:
        self.manager.current = "game_ui"
        messenger.send("system.input.raycaster_on")

    def switch_to_load_screen(self, _: Any) -> None:
        messenger.send("ui.update.ui.show_load")

    def switch_to_save_screen(self, _: Any) -> None:
        messenger.send("ui.update.ui.show_save")

    def open_browser_to_code(self, _: Optional[Button] = None) -> None:
        import webbrowser

        from system.vars import REPOSITORY

        webbrowser.open_new_tab(REPOSITORY)

    def exit(self, _: Optional[Button] = None) -> None:
        messenger.send("game.input.user.quit_game")

    def hide(self, _: Optional[Button] = None) -> None:
        if self.layout is not None:
            self.layout.visible = False  # type: ignore
        self.to_game_screen()

    def show(self) -> None:
        if self.layout is not None:
            self.layout.visible = True  # type: ignore
