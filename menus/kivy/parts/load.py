from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup

from managers.entity import EntityManager
from menus.kivy.elements.button_value import ButtonValue
from menus.kivy.elements.list_item import ListItem
from menus.kivy.elements.popup import CollisionPreventionMixin
from menus.kivy.elements.sticky_text_input import StickyTextInput
from menus.kivy.parts.city import ClippingScrollList

if TYPE_CHECKING:
    from main import SCIV


class LoadPopup(Popup, CollisionPreventionMixin, DirectObject):
    def __init__(self, base: "SCIV", auto_dismiss=False, **kwargs):
        super().__init__(
            title="Load Game",
            base=base,
            auto_dismiss=auto_dismiss,
            size_hint=(0.8, 0.8),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            **kwargs,
        )
        self.base: "SCIV" = base

        # Use (1, 1) so the layout expands to fill the entire popup
        self.main_layout = GridLayout(orientation="lr-tb", rows=3, cols=2, spacing=10, size_hint=(1, 1))

        self.scroll_view: Optional[ClippingScrollList] = None
        self.scroll_grid: Optional[GridLayout] = None

        self.details_layout: Optional[GridLayout] = None

        self.spacer: Optional[Label] = None

        self.name_input_container: Optional[GridLayout] = None
        self.name_input_label: Optional[Label] = None
        self.name_input: Optional[StickyTextInput] = None

        self.footer_load_button: Optional[ButtonValue] = None
        self.footer_cancel_button: Optional[ButtonValue] = None

        self.items: List[ListItem] = []

        self.title_label: Optional[Label] = None
        self.hash_label: Optional[Label] = None
        self.entities_label: Optional[Label] = None
        self.size_label: Optional[Label] = None

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
        # Give the left scroll panel a size_hint_x so it occupies the left portion
        self.scroll_view = ClippingScrollList(size_hint=(0.6, 0.95), do_scroll_x=False, do_scroll_y=True)
        self.items = []

        for i, save_game in enumerate(self.get_save_games()):
            item_button = ListItem(
                text=save_game,
                value=save_game,
                size_hint=(1, None),
                height=40,
                background_color=(1, 1, 1, 0.3),
            )
            item_button.bind(on_release=self.on_item_select)
            self.items.append(item_button)
            self.scroll_view.add_widget(item_button)

        self.main_layout.add_widget(self.scroll_view)

    def rebuild(self):
        self.rebuild_left_scroll_view()

    def rebuild_left_scroll_view(self) -> None:
        if self.scroll_view is None:
            return

        self.scroll_view.clear_widgets()
        self.items = []  # Clear the old list

        # Gather save game items with datetime.
        save_games_with_dt: list[tuple[datetime, str, dict]] = []
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
            self.items.append(item_button)  # Update the list
            self.scroll_view.add_widget(item_button)

    def on_item_select(self, instance: ListItem):
        self.select_item(str(instance.value))

    def on_press(self, instance: ListItem):
        self.clear_item_background_color()

        instance.background_color = (1, 1, 1, 0.5)

    def clear_item_background_color(self):
        if self.scroll_view is None:
            return

        for item in self.items:
            item.background_color = (1, 1, 1, 0.3)

    def select_item(self, item_value: str):
        if not self.name_input:
            return

        self.name_input.text = item_value
        self.update_details(item_value)

    def update_details(self, item_value: str):
        save_game = self.get_save_game(item_value)

        if (
            not save_game
            or not self.title_label
            or not self.hash_label
            or not self.entities_label
            or not self.size_label
        ):
            return

        self.title_label.text = f"Load {item_value}"
        self.hash_label.text = ""
        self.entities_label.text = f"Entities: {save_game['stats']['total_entities_registered']}"
        self.size_label.text = f"Size: {save_game['loaded_data_length']} bytes"

    def build_right_info_panel(self):
        self.details_layout = GridLayout(cols=1, spacing=5, size_hint=(0.35, 1))

        # Example labels
        self.title_label = Label(text="Load saved games", size_hint=(1, None), height=40, font_size="18sp")
        self.hash_label = Label(text="")
        self.entities_label = Label(text="")
        self.size_label = Label(text="")

        self.details_layout.add_widget(self.title_label)
        self.details_layout.add_widget(self.hash_label)
        self.details_layout.add_widget(self.entities_label)
        self.details_layout.add_widget(self.size_label)

        self.main_layout.add_widget(self.details_layout)

    def build_save_name_input(self):
        self.name_input_container = GridLayout(cols=2, size_hint=(0.6, None), height=40)

        self.name_input_label = Label(text="Load Name:", size_hint=(0.2, None), height=40, halign="left")

        self.name_input = StickyTextInput(size_hint=(0.75, None), height=40)
        self.name_input.disabled = True

        self.name_input_container.add_widget(self.name_input_label)
        self.name_input_container.add_widget(self.name_input)

        self.spacer = Label(size_hint=(0.4, None), height=40)

        self.main_layout.add_widget(self.name_input_container)
        self.main_layout.add_widget(self.spacer)

    def build_footer(self):
        self.footer_load_button = ButtonValue(text="Load", size_hint=(1, None), height=50)
        self.footer_load_button.bind(on_release=self.on_load_game)

        self.footer_cancel_button = ButtonValue(text="Cancel", size_hint=(0.35, None), height=50)
        self.footer_cancel_button.bind(on_release=self.on_cancel)

        self.main_layout.add_widget(self.footer_load_button)
        self.main_layout.add_widget(self.footer_cancel_button)

    def on_load_game(self, instance): ...

    def on_cancel(self, instance):
        self.close_popup()

    def open_popup(self):
        self.rebuild()
        self.open()
        self.register_non_collidable(self)
        self.accept("escape", self.close_popup)
        MessengerGlobal.messenger.send("system.input.disable_zoom")
        MessengerGlobal.messenger.send("system.input.disable_control")
        MessengerGlobal.messenger.send("system.input.camera_lock")

    def close_popup(self):
        self.dismiss()
        self.unregister_non_collidable(self)
        self.ignore("escape")
        MessengerGlobal.messenger.send("system.input.enable_zoom")
        MessengerGlobal.messenger.send("system.input.enable_control")
        MessengerGlobal.messenger.send("system.input.camera_unlock")
        MessengerGlobal.messenger.send("system.input.raycaster_on")
