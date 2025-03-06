from enum import Enum
from logging import Logger
from typing import Optional
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from menus.kivy.elements.button_value import ButtonValue
from kivy.uix.spinner import Spinner
from menus.kivy.mixins.collidable import CollisionPreventionMixin
from direct.showbase.MessengerGlobal import messenger


class MapActionsValues(Enum):
    NONE = "None"
    SMALL_BIG_ICONS = "Small+Big Icons"
    SMALL_ICONS = "Small Icons"
    BIG_ICONS = "Big Icons"
    ALL_IN_RADIUS = "All in Radius"


class LenseOptionsValues(Enum):
    NONE = "None"
    UNITS = "Units"
    WATER = "Water"
    RESOURCES = "Resources"


class DebugUIOptionsValues(Enum):
    NONE = "None"
    DEBUG = "Debug"
    STATS = "Stats"
    ACTIONS = "Actions"
    DEBUG_AND_STATS = "Debug+Stats"
    DEBUG_AND_ACTIONS = "Debug+Actions"
    ALL_DEBUG_UI = "All Debug UI"


class DebugActions(
    BoxLayout,
    CollisionPreventionMixin,
):
    def __init__(self, base, logger: Logger, background_color=(0, 0, 0, 0), border=(0, 0, 0, 0), **kwargs):
        self.background_color = background_color
        self.border = border
        self.background_image = None
        super(BoxLayout).__init__(**kwargs)
        super(CollisionPreventionMixin, self).__init__(**kwargs)
        self.base = base
        self.frame: Optional[BoxLayout] = None
        self.logger: Logger = logger.getChild("screen.parts.debug_actions")

        self.toggle_big_icons: Optional[Button] = None
        self.lenses_dropdown: Optional[Spinner] = None
        self.map_actions: Optional[Spinner] = None
        self.debug_ui_spinner: Optional[Spinner] = None
        self.lenses_dropdown_open: bool = False

    def build(self) -> BoxLayout:
        # --- Action Bar (Bottom Centered) ---
        self.frame = BoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            width=1000,
            height=200,
            spacing=10,
            pos_hint={"center_x": 0.5, "y": 0.92},
        )

        self.lenses_dropdown = Spinner(
            text="Lenses(None)",
            size_hint=(None, None),
            width=150,
            height=80,
        )

        if self.lenses_dropdown._dropdown is None:
            raise ValueError("Dropdown is not initialized.")

        self.lenses_dropdown._dropdown.bind(on_select=self.on_lense_change_request)
        self.lenses_dropdown.values = [str(v.value) for _, v in LenseOptionsValues.__members__.items()]
        self.frame.add_widget(self.lenses_dropdown)

        self.map_actions = Spinner(
            text="Resources (Big Only)",
            size_hint=(None, None),
            width=150,
            height=80,
        )

        if self.map_actions._dropdown is None:
            raise ValueError("Dropdown is not initialized.")

        self.map_actions._dropdown.bind(on_select=self.on_resource_ui_change_request)
        self.map_actions.values = [str(v.value) for _, v in MapActionsValues.__members__.items()]
        self.frame.add_widget(self.map_actions)

        items = {str(v.value): k for k, v in DebugUIOptionsValues.__members__.items()}
        self.debug_ui_spinner = Spinner(
            text="Debug UI (ALL)",
            size_hint=(None, None),
            width=150,
            height=80,
            on_select=self.on_debug_ui_change_request,
            values=items,
        )

        self.register_non_collidable(self.debug_ui_spinner)

        if self.debug_ui_spinner._dropdown is None:
            raise ValueError("Dropdown is not initialized.")

        elif self.debug_ui_spinner._dropdown.container is not None:
            for child in self.debug_ui_spinner._dropdown.container.children:
                self.register_non_collidable(child)
            self.debug_ui_spinner._dropdown.bind(on_select=self.on_debug_ui_change_request)
            self.frame.add_widget(self.debug_ui_spinner)

        return self.frame

    def on_lense_change_request(self, instance: Button, selected_text: str):
        # 'instance.text' will now be one of "None", "Units", "Water", "Resources"
        state_enum = next((_member for _member in LenseOptionsValues if _member.value == selected_text), None)
        if state_enum is None:
            self.logger.error(f"No matching state for {instance}")
            return

        self.logger.info(f"Lense change requested to state {str(state_enum.value)}.")
        messenger.send("ui.update.ui.lense_change", [state_enum])

    def on_resource_ui_change_request(self, instance: Button, selected_text: str):
        state_enum = next(
            (_member for _member in MapActionsValues if _member.value.lower() == selected_text.lower()), None
        )

        if state_enum is None:
            self.logger.error(f"No matching state for {instance.text}")
            return

        self.logger.info(f"Resource UI change requested to state {str(state_enum.value)}.")
        messenger.send("ui.update.ui.resource_ui_change", [state_enum])

    def on_debug_ui_change_request(self, instance: ButtonValue, selected_text: str):
        state_enum = next(
            (_member for _member in DebugUIOptionsValues if _member.value.lower() == selected_text.lower()), None
        )
        if state_enum is None:
            self.logger.error(f"No matching state for {instance.text}")
            return

        self.logger.info(f"Debug UI change requested to state {str(state_enum.name)}.")
        messenger.send("ui.update.ui.debug_ui_toggle", [state_enum])

    def get_frame(self) -> BoxLayout:
        if not self.frame:
            raise ValueError("Action Bar frame has not been built yet.")
        return self.frame

    def add_button(self, button: Button):
        self.get_frame().add_widget(button)
        return button

    def remove_button(self, button: Button):
        self.get_frame().remove_widget(button)
        return button

    def clear_buttons(self):
        self.get_frame().clear_widgets()
        return self.frame
