from typing import TYPE_CHECKING, Any, Optional

from direct.showbase.DirectObject import DirectObject
from direct.showbase.MessengerGlobal import messenger
from kivy.app import Widget
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen

from managers.i18n import t_
from menus.kivy.mixins.collidable import CollisionPreventionMixin

if TYPE_CHECKING:
    from game import SCIV


class PauseMenu(Popup, CollisionPreventionMixin, DirectObject):
    def __init__(self, base: "SCIV", **kwargs: Any):
        CollisionPreventionMixin.__init__(self, base=base, **kwargs)
        Popup.__init__(self, base=base, **kwargs)  # type: ignore
        DirectObject.__init__(self)

        self.title = str(t_("ui.player_ui.pause.popup.title"))
        self.size_hint = (0.5, 0.6)
        self.auto_dismiss = False
        self._base: "SCIV" = base

        self.container: Optional[BoxLayout] = None
        self.rect: Optional[Rectangle] = None
        self.title_label: Optional[Label] = None
        self.resume_btn: Optional[Button] = None
        self.reroll_btn: Optional[Button] = None
        self.save_btn: Optional[Button] = None
        self.load_btn: Optional[Button] = None
        self.options_btn: Optional[Button] = None
        self.main_menu_btn: Optional[Button] = None
        self.quit_btn: Optional[Button] = None
        self.is_open: bool = False
        self.register()

    def register(self):
        self.accept("ui.update.ui.show_pause", self.open)
        self.accept("ui.update.ui.hide_pause", self.dismiss)

    def build_widget(self):
        self.container = BoxLayout(
            orientation="vertical",
            padding=(10, 10),
            spacing=10,
        )

        self.container.canvas.before.add(Color(0, 0, 0, 0.7))
        self.rect = Rectangle(size=self.container.size, pos=self.container.pos)  # type: ignore
        self.container.canvas.before.add(self.rect)

        def update_rect(instance: Widget, value: Any):
            self.rect.size = instance.size  # type: ignore
            self.rect.pos = instance.pos  # type: ignore

        self.container.bind(size=update_rect, pos=update_rect)  # type: ignore

        self.title_label = Label(
            text=str(t_("ui.player_ui.pause.popup.title")),
            font_size=40,
            size_hint=(1, None),
            height=40,
        )
        self.container.add_widget(self.title_label)  # type: ignore

        self.resume_btn = Button(text=str(t_("ui.player_ui.pause.resume")), size_hint=(1, None), height=50)
        self.resume_btn.bind(on_release=self.dismiss)
        self.container.add_widget(self.resume_btn)  # type: ignore

        self.reroll_btn = Button(text=str(t_("ui.player_ui.pause.reroll")), size_hint=(1, None), height=50)
        self.reroll_btn.bind(on_release=self.on_reroll)
        self.container.add_widget(self.reroll_btn)  # type: ignore

        self.save_btn = Button(text=str(t_("ui.player_ui.pause.save")), size_hint=(1, None), height=50)
        self.save_btn.bind(on_release=self.save_game)
        self.container.add_widget(self.save_btn)  # type: ignore

        self.load_btn = Button(text=str(t_("ui.player_ui.pause.load")), size_hint=(1, None), height=50)
        self.load_btn.bind(on_release=self.load_game)
        self.container.add_widget(self.load_btn)  # type: ignore

        self.options_btn = Button(text=str(t_("ui.player_ui.pause.options")), size_hint=(1, None), height=50)
        self.options_btn.bind(on_release=self.open_options)
        self.container.add_widget(self.options_btn)  # type: ignore

        self.main_menu_btn = Button(text=str(t_("ui.player_ui.pause.main_menu")), size_hint=(1, None), height=50)
        self.main_menu_btn.bind(on_release=self.return_to_main_menu)
        self.container.add_widget(self.main_menu_btn)  # type: ignore

        self.quit_btn = Button(text=str(t_("ui.player_ui.pause.quit")), size_hint=(1, None), height=50)
        self.quit_btn.bind(on_release=self.quit_game)
        self.container.add_widget(self.quit_btn)  # type: ignore

        self.add_widget(self.container)  # type: ignore
        self.register_non_collidable(self.container)

    def save_game(self, instance: Widget):
        messenger.send("ui.update.ui.show_save")

    def load_game(self, instance: Widget):
        messenger.send("ui.update.ui.show_load")

    def open_options(self, instance: Widget):
        print("Opening options...")  # @TODO: Implement this method

    def return_to_main_menu(self, instance: Widget):
        messenger.send("ui.request_main_menu")

    def quit_game(self, instance: Widget):
        messenger.send("game.input.user.quit_game")

    def open(self):
        if self.container is None:
            raise ValueError("Container is not built yet.")

        self.is_open = True
        self.register_non_collidable(self.container)
        super().open()  # type: ignore

    def dismiss(self, _: Any = None) -> None:
        if self.container is None:
            raise ValueError("Container is not built yet.")

        self.is_open = False
        self.unregister_non_collidable(self.container)
        super().dismiss()  # type: ignore

    def on_reroll(self, _: Any = None) -> None:
        messenger.send("ui.request.reroll")


class PauseScreen(Screen):
    def __init__(self, base: "SCIV", **kwargs: Any):
        super().__init__(**kwargs)  # type: ignore
        self.pause_menu = PauseMenu(base=base)
        self.build: bool = False
        self.build_screen()

    def build_screen(self):
        if self.build is True:
            return
        self.build = True
        return self.pause_menu.build_widget()

    def on_enter(self, *args: Any):
        self.pause_menu.open()

    def on_leave(self, *args: Any):
        self.pause_menu.dismiss()
