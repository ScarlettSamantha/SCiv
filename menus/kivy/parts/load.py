from typing import TYPE_CHECKING, Optional

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

from menus.kivy.elements.button_value import ButtonValue
from menus.kivy.elements.list_item import ListItem
from menus.kivy.elements.popup import CollisionPreventionMixin
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
        self.name_input: Optional[TextInput] = None

        self.footer_load_button: Optional[ButtonValue] = None
        self.footer_cancel_button: Optional[ButtonValue] = None

        self.build()
        self.add_widget(self.main_layout)

    def build(self):
        self.build_left_scroll_view()
        self.build_right_info_panel()
        self.build_save_name_input()
        self.build_footer()

    def build_left_scroll_view(self):
        # Give the left scroll panel a size_hint_x so it occupies the left portion
        self.scroll_view = ClippingScrollList(size_hint=(0.6, 0.95), do_scroll_x=False, do_scroll_y=True)

        for i in range(35):
            background_color = (1, 1, 1, 0.3) if i % 2 == 0 else (1, 1, 1, 0.4)
            item_button = ListItem(
                text=f"List Item {i + 1}",
                value=str(i),
                size_hint=(1, None),
                height=40,
                background_color=background_color,
            )
            item_button.bind(on_release=self.on_item_select)
            self.scroll_view.add_widget(item_button)

        self.main_layout.add_widget(self.scroll_view)

    def on_item_select(self, instance: ButtonValue):
        self.select_item(str(instance.value))

    def select_item(self, item_value: str): ...

    def build_right_info_panel(self):
        # We'll make the right panel 0.4 to fill the remainder
        self.details_layout = GridLayout(cols=1, spacing=5, size_hint=(0.35, 1))

        # Example labels
        title_label = Label(text="Details", size_hint=(1, None), height=40, font_size="18sp")
        stat_label_1 = Label(text="Some info: 0")
        stat_label_2 = Label(text="More info: 42")
        stat_label_3 = Label(text="Extra info: ???")

        self.details_layout.add_widget(title_label)
        self.details_layout.add_widget(stat_label_1)
        self.details_layout.add_widget(stat_label_2)
        self.details_layout.add_widget(stat_label_3)

        self.main_layout.add_widget(self.details_layout)

    def build_save_name_input(self):
        self.name_input_container = GridLayout(cols=2, size_hint=(0.6, None), height=40)

        self.name_input_label = Label(text="Load Name:", size_hint=(0.2, None), height=40, halign="left")

        self.name_input = TextInput(size_hint=(0.75, None), height=40)

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
