from typing import TYPE_CHECKING, Optional

from direct.showbase.MessengerGlobal import messenger
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen

from managers.i18n import t_
from menus.kivy.mixins.collidable import CollisionPreventionMixin

if TYPE_CHECKING:
    from main import SCIV


class PauseMenu(Popup, CollisionPreventionMixin):
    def __init__(self, base: "SCIV", **kwargs):
        CollisionPreventionMixin.__init__(self, base=base, **kwargs)
        Popup.__init__(self, base=base, **kwargs)

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

    def build_widget(self):
        self.container = BoxLayout(
            orientation="vertical",
            padding=(10, 10),
            spacing=10,
        )

        self.container.canvas.before.add(Color(0, 0, 0, 0.7))
        self.rect = Rectangle(size=self.container.size, pos=self.container.pos)
        self.container.canvas.before.add(self.rect)

        def update_rect(instance, value):
            self.rect.size = instance.size  # type: ignore
            self.rect.pos = instance.pos  # type: ignore

        self.container.bind(size=update_rect, pos=update_rect)

        self.title_label = Label(
            text=str(t_("ui.player_ui.pause.popup.title")),
            font_size=40,
            size_hint=(1, None),
            height=40,
        )
        self.container.add_widget(self.title_label)

        self.resume_btn = Button(text=str(t_("ui.player_ui.pause.resume")), size_hint=(1, None), height=50)
        self.resume_btn.bind(on_release=self.dismiss)
        self.container.add_widget(self.resume_btn)

        self.save_btn = Button(text="Save", size_hint=(1, None), height=50)
        self.save_btn.bind(on_release=self.save_game)
        self.container.add_widget(self.save_btn)

        self.load_btn = Button(text=str(t_("ui.player_ui.pause.load")), size_hint=(1, None), height=50)
        self.load_btn.bind(on_release=self.load_game)
        self.container.add_widget(self.load_btn)

        self.options_btn = Button(text=str(t_("ui.player_ui.pause.options")), size_hint=(1, None), height=50)
        self.options_btn.bind(on_release=self.open_options)
        self.container.add_widget(self.options_btn)

        self.main_menu_btn = Button(text=str(t_("ui.player_ui.pause.main_menu")), size_hint=(1, None), height=50)
        self.main_menu_btn.bind(on_release=self.return_to_main_menu)
        self.container.add_widget(self.main_menu_btn)

        self.quit_btn = Button(text=str(t_("ui.player_ui.pause.quit")), size_hint=(1, None), height=50)
        self.quit_btn.bind(on_release=self.quit_game)
        self.container.add_widget(self.quit_btn)

        self.add_widget(self.container)
        self.register_non_collidable(self.container)

    def save_game(self, instance):
        messenger.send("ui.update.ui.show_save")

    def load_game(self, instance):
        messenger.send("ui.update.ui.show_load")

    def open_options(self, instance):
        print("Opening options...")

    def return_to_main_menu(self, instance):
        messenger.send("ui.request_main_menu")

    def quit_game(self, instance):
        messenger.send("game.input.user.quit_game")

    def open(self):
        self.register_non_collidable(self.container)
        super().open()

    def dismiss(self, _=None):
        self.unregister_non_collidable(self.container)
        super().dismiss()

    def on_reroll(self, _=None):
        messenger.send("ui.request.reroll")


class PauseScreen(Screen):
    def __init__(self, base: "SCIV", **kwargs):
        super().__init__(**kwargs)
        self.pause_menu = PauseMenu(base=base)
        self.build: bool = False
        self.build_screen()

    def build_screen(self):
        if self.build is True:
            return
        self.build = True
        return self.pause_menu.build_widget()

    def on_enter(self, *args):
        self.pause_menu.open()

    def on_leave(self, *args):
        self.pause_menu.dismiss()
