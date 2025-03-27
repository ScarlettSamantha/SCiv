from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup

from managers.entity import EntityManager
from managers.player import PlayerManager
from menus.kivy.elements.button_value import ButtonValue
from menus.kivy.elements.list_item import ListItem
from menus.kivy.elements.popup import CollisionPreventionMixin
from menus.kivy.elements.sticky_text_input import StickyTextInput
from menus.kivy.parts.city import ClippingScrollList

if TYPE_CHECKING:
    from main import SCIV


class SavePopup(Popup, CollisionPreventionMixin, DirectObject):
    def __init__(self, base: "SCIV", auto_dismiss=False, **kwargs):
        super().__init__(
            title="Save Game",
            base=base,
            auto_dismiss=auto_dismiss,
            size_hint=(0.8, 0.8),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            disable_zoom=False,
            **kwargs,
        )
        self.base: "SCIV" = base
        self.manager = self.base.ui_manager

        # Use (1, 1) so the layout expands to fill the entire popup
        self.main_layout = GridLayout(orientation="lr-tb", rows=3, cols=2, spacing=10, size_hint=(1, 1))

        self.scroll_view: Optional[ClippingScrollList] = None
        self.scroll_grid: Optional[GridLayout] = None

        self.details_layout: Optional[GridLayout] = None

        self.spacer: Optional[Label] = None

        self.name_input_container: Optional[GridLayout] = None
        self.name_input_label: Optional[Label] = None
        self.name_input: Optional[StickyTextInput] = None

        self.title_label: Optional[Label] = None

        self.footer_save_button: Optional[ButtonValue] = None
        self.footer_cancel_button: Optional[ButtonValue] = None

        self.build()
        self.add_widget(self.main_layout)

    def build(self):
        self.build_left_scroll_view()
        self.build_right_info_panel()
        self.build_save_name_input()
        self.build_footer()

    def get_save_games(self) -> List[str]:
        save_game_session: List[str] = EntityManager.get_instance().get_all_session()

        return save_game_session

    def get_save_game(self, name: str) -> Dict[str, Any] | None:
        return EntityManager.get_instance().get_session_data(name)

    def build_left_scroll_view(self):
        self.scroll_view = ClippingScrollList(size_hint=(0.6, 0.95), do_scroll_x=False, do_scroll_y=True)

        for i, save_game in enumerate(self.get_save_games()):
            item_button = ListItem(
                text=save_game,
                value=save_game,
                size_hint=(1, None),
                height=40,
                background_color=(1, 1, 1, 0.3),
            )
            item_button.bind(on_release=self.on_item_select)
            item_button.bind(on_press=self.on_press)
            self.scroll_view.add_widget(item_button)

        self.main_layout.add_widget(self.scroll_view)

    def rebuild(self):
        self.rebuild_left_scroll_view()
        self.rebuild_right_info_panel()
        self.rebuild_input()
        self.rebuild_label()

    def rebuild_input(self):
        if self.name_input is None:
            return

        self.name_input.text = PlayerManager.player().name

    def rebuild_right_info_panel(self):
        if self.title_label is None:
            return

        self.title_label.text = ""

    def rebuild_left_scroll_view(self) -> None:
        if self.scroll_view is None:
            return

        self.scroll_view.clear_widgets()

        # Gather save game items with datetime.
        save_games_with_dt: List[tuple[datetime, str, Dict]] = []
        for save_game in self.get_save_games():
            save_game_data = self.get_save_game(save_game)
            if save_game_data is None:
                continue

            save_time: str = save_game_data["saver"]["save_time"]
            save_date_time: datetime = datetime.fromisoformat(save_time)
            save_games_with_dt.append((save_date_time, save_game, save_game_data))

        # Sort by datetime descending (newest first).
        save_games_with_dt.sort(key=lambda item: item[0], reverse=True)

        for save_date_time, save_game, _ in save_games_with_dt:
            item_button = ListItem(
                text=f"{save_game} - {save_date_time.strftime('%Y-%m-%d %H:%M:%S')}",
                value=save_game,
                size_hint=(1, None),
                height=40,
                background_color=(1, 1, 1, 0.3),
            )
            item_button.bind(on_release=self.on_item_select)
            item_button.bind(on_press=self.on_press)
            self.scroll_view.add_widget(item_button)

    def rebuild_label(self, *args, **kwargs):
        if self.name_input_label is None or self.name_input is None:
            return

        if self.name_input.text in self.get_save_games():
            self.name_input_label.text = "Save Name [color=ff3333](!Overwrite!)[/color]:"
            self.name_input_label.markup = True
        else:
            self.name_input_label.text = "Save Name:"

    def on_item_select(self, instance: ListItem):
        instance.background_color = (1, 1, 1, 0.3)
        self.select_item(str(instance.value))

        if self.title_label is not None:
            self.title_label.text = str(instance.value)

        self.rebuild_label()

    def on_press(self, instance):
        instance.background_color = (1, 1, 1, 0.5)

    def select_item(self, item_value: str):
        if self.name_input is None:
            return

        self.name_input.text = item_value

    def build_right_info_panel(self):
        # We'll make the right panel 0.4 to fill the remainder
        self.details_layout = GridLayout(cols=1, spacing=5, size_hint=(0.35, 1))

        # Example labels
        self.title_label = Label(text="", size_hint=(1, None), height=40, font_size="18sp")

        self.details_layout.add_widget(self.title_label)
        self.main_layout.add_widget(self.details_layout)

    def build_save_name_input(self):
        self.name_input_container = GridLayout(cols=2, size_hint=(0.6, None), height=40)

        self.name_input_label = Label(text="Save Name:", size_hint=(0.2, None), height=40, halign="left")

        self.name_input = StickyTextInput(text="?", size_hint=(0.75, None), height=40)
        self.name_input.bind(on_press=self.on_name_input_press)
        self.name_input.bind(on_complete=self.rebuild_label)
        self.name_input.bind(on_text_validate=self.rebuild_label)

        self.name_input_container.add_widget(self.name_input_label)
        self.name_input_container.add_widget(self.name_input)

        self.spacer = Label(size_hint=(0.4, None), height=40)

        self.main_layout.add_widget(self.name_input_container)
        self.main_layout.add_widget(self.spacer)

    def build_footer(self):
        self.footer_save_button = ButtonValue(text="Save", size_hint=(1, None), height=50)
        self.footer_save_button.bind(on_release=self.on_save_game)

        self.footer_cancel_button = ButtonValue(text="Cancel", size_hint=(0.35, None), height=50)
        self.footer_cancel_button.bind(on_release=self.on_cancel)

        self.main_layout.add_widget(self.footer_save_button)
        self.main_layout.add_widget(self.footer_cancel_button)

    def on_save_game(self, instance):
        if self.name_input is None:
            return
        MessengerGlobal.messenger.send("ui.request.save_game", [self.name_input.text])

        Clock.schedule_once(lambda dt: self.rebuild(), 2)  # 2 second delay to give the disk time to write

    def on_name_input_press(self, instance):
        if self.name_input is None:
            return
        self.name_input.focus = True

    def on_cancel(self, instance):
        self.close_popup()

    def rebuild_label_task(self, task: Task):
        self.rebuild_label()
        return task.cont

    def open_popup(self):
        self.rebuild()
        self.open()
        self.register_non_collidable(self)
        self.accept("escape", self.close_popup)
        MessengerGlobal.messenger.send("system.input.disable_zoom")
        MessengerGlobal.messenger.send("system.input.disable_control")
        MessengerGlobal.messenger.send("system.input.camera_lock")
        self.addTask(self.rebuild_label_task, "rebuild_label", delay=2)

    def close_popup(self):
        self.dismiss()
        self.unregister_non_collidable(self)
        self.ignore("escape")
        MessengerGlobal.messenger.send("system.input.camera_unlock")  # unlock first
        MessengerGlobal.messenger.send("system.input.enable_zoom")
        MessengerGlobal.messenger.send("system.input.enable_control")
        MessengerGlobal.messenger.send("system.input.raycaster_on")
        self.manager.set_screen("game_ui")
        self.removeTask("rebuild_label")
