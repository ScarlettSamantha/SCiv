from math import floor
from typing import TYPE_CHECKING, Any, Optional

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from kivy.app import Widget
from kivy.graphics import Color, Rectangle
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout

from exceptions.invalid_pregame_condition import InvalidPregameCondition
from gameplay.resources.core.basic.culture import Culture
from gameplay.resources.core.basic.faith import Faith
from gameplay.resources.core.basic.gold import Gold
from gameplay.resources.core.basic.science import Science
from helpers.cache import Cache
from helpers.colors import Tuple4f
from helpers.placeholder import Placeholder
from managers.player import PlayerManager
from managers.turn import Turn
from menus.kivy.elements.button_self_resizable import SelfResizableButton
from menus.screens.loading import ImageLabel
from sciv.helpers.windows import WindowsHelper

if TYPE_CHECKING:
    from game import OpenCiv


class BaseButton(SelfResizableButton):
    placeholder: str = Placeholder.getPlaceholderImagePathSmallIcon()

    def _update_image(self, instance: Widget, value: str) -> None:
        if value:
            self.image_widget.source = value
            self.image_widget.opacity = 1
        else:
            placeholder_path = str(Cache.get_icon_atlas().get_real_path_for_virtual_path(self.placeholder))

            if WindowsHelper.is_windows():
                placeholder_path = WindowsHelper.unix_to_win32_path(placeholder_path)

            self.image_widget.source = placeholder_path
            self.image_widget.opacity = 0
            self.image_widget.width = 0
        self._update_size()


class ResearchButton(BaseButton):
    placeholder: str = str(Cache.get_icon_atlas().get_real_path_for_virtual_path(Science.icon))

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)


class CultureButton(BaseButton):
    placeholder: str = str(Cache.get_icon_atlas().get_real_path_for_virtual_path(Culture.icon))

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)


class TopBar(BoxLayout, DirectObject):
    def __init__(
        self,
        base: "OpenCiv",
        background_color: Tuple4f = (0, 0, 0, 0.9),
        border: Tuple4f = (0, 0, 0, 0),
        *args: Any,
        **kwargs: Any,
    ):
        # Force a horizontal box layout at the root
        super().__init__(orientation="horizontal", size_hint=(1, None), height=30, *args, **kwargs)

        self.is_build: bool = False
        self.pos_hint = {"center_x": 0.5, "top": 1}
        self.base: "OpenCiv" = base
        self.background_color: Tuple4f = background_color
        self.border: Tuple4f = border

        self.research_label: Optional[ResearchButton] = None
        self.gold_label: Optional[ImageLabel] = None
        self.faith_label: Optional[ImageLabel] = None
        self.culture_label: Optional[CultureButton] = None
        self.turn_label: Optional[ImageLabel] = None

        # Build 3 sub-boxes: left 30%, center 40%, right 30%
        self.left_container = BoxLayout(size_hint=(0.3, 1), orientation="horizontal", padding=(5, 0))
        self.add_widget(self.left_container)  # type: ignore

        self.center_anchor = AnchorLayout(size_hint=(0.4, 1), anchor_x="center", anchor_y="center")
        self.center_container = BoxLayout(orientation="horizontal", spacing=10, size_hint=(None, None))
        # Let the BoxLayout’s width shrink or grow to fit children
        self.center_container.bind(  # type: ignore
            minimum_width=self.center_container.setter("width"),  # type: ignore
            minimum_height=self.center_container.setter("height"),  # type: ignore
        )
        self.center_anchor.add_widget(self.center_container)  # type: ignore
        self.add_widget(self.center_anchor)  # type: ignore

        self.right_container = BoxLayout(size_hint=(0.3, 1), orientation="horizontal", padding=(5, 0))
        self.add_widget(self.right_container)  # type: ignore

        # Draw background rectangle
        with self.canvas.before:
            Color(*self.background_color)
            self.rect = Rectangle(size=self.size, pos=self.pos)  # type: ignore

        self.bind(size=self._update_rect, pos=self._update_rect)  # type: ignore

        # Register event and build the bar
        self.register()

    def _update_rect(self, *_):
        self.rect.size = self.size  # type: ignore
        self.rect.pos = self.pos  # type: ignore

    def register(self):
        self.accept("ui.update.ui.refresh_top_bar", self.update)

    def build(self):
        if self.is_build:
            return self

        # Create labels
        self.research_label = ResearchButton(
            text="Researching: None",
            size_hint=(None, 1),
            background_color=(0, 0, 0, 0),
        )
        self.research_label.bind(on_press=self.on_click_research)  # type: ignore
        self.culture_label = CultureButton(
            text="Culture: 0",
            size_hint=(None, 1),
            background_color=(0, 0, 0, 0),
        )

        gold_path = Gold.icon
        faith_path = Faith.icon
        turn_path = "assets/icons/turn.png"

        self.gold_label = ImageLabel(
            text="Gold: 0",
            size_hint=(None, 1),
            width=100,
            img_y_offset=-0.05,
            img_source=gold_path,
        )

        self.faith_label = ImageLabel(
            text="Faith: 0",
            size_hint=(None, 1),
            width=100,
            img_source=faith_path,
        )

        self.turn_label = ImageLabel(
            text="Turn: 0",
            size_hint=(None, 1),
            width=100,
            img_source=turn_path,
        )

        # Add them to the respective container
        # Left container can hold your "research" text
        self.left_container.add_widget(self.research_label)  # type: ignore
        self.left_container.add_widget(self.culture_label)  # type: ignore

        # Center container for turn, culture, gold, etc.
        self.center_container.add_widget(self.gold_label)  # type: ignore
        self.center_container.add_widget(self.turn_label)  # type: ignore
        self.center_container.add_widget(self.faith_label)  # type: ignore

        self.is_build = True
        return self

    def update(self):
        """Refresh labels with new values."""
        try:
            player = PlayerManager.session_player()
            turn = Turn.get_singleton_instance().turn
        except InvalidPregameCondition:
            if self.research_label is not None:
                self.research_label.text = "Researching: None"
            if self.culture_label is not None:  # type: ignore
                self.culture_label.text = "Culture: 0"
            if self.gold_label is not None:
                self.gold_label.text = "Gold: 0"
            if self.faith_label is not None:
                self.faith_label.text = "Faith: 0"
            if self.turn_label is not None:
                self.turn_label.text = "Turn: 0"
            return

        if any(
            label is None
            for label in (
                self.research_label,
                self.culture_label,
                self.gold_label,
                self.faith_label,
                self.turn_label,
            )
        ):
            raise ValueError("Top Bar labels have not been built yet.")

        if (current_tech := player.tech.current_tech()) is None and self.research_label is not None:
            self.research_label.text = "Researching: None"
        elif current_tech is not None and self.research_label is not None:
            tech_icon = str(current_tech.get_icon())
            tech_icon: str = str(Cache.get_icon_atlas().get_real_path_for_virtual_path(str(tech_icon)))

            self.research_label.text = f"Researching: {str(current_tech.name)}({str(player.tech.current_science)} / {str(player.tech.needed_science)})"  # type: ignore
            self.research_label.image_source = str(  # type: ignore
                Cache.get_icon_atlas().get_real_path_for_virtual_path(str(current_tech.get_icon()))
            )  # type: ignore
        self.culture_label.text = f"Culture: {floor(player.culture.culture.value)}"  # type: ignore

        self.gold_label.text = f"Gold: {floor(player.gold.gold.value)}"  # type: ignore
        self.faith_label.text = f"Faith: {floor(player.faith.faith.value)}"  # type: ignore

        self.turn_label.text = f"Turn: {turn}"  # type: ignore

    def reset(self):
        """Rebuild the top bar from scratch."""
        self.clear_widgets()
        self.build()

    def add_widget_item(self, widget: Widget) -> Optional[Widget]:
        """Add a widget somewhere on the bar if you want."""
        # Example: add to right container
        self.right_container.add_widget(widget)  # type: ignore
        return widget

    def remove_widget_item(self, widget: Widget) -> Optional[Widget]:
        """Remove a widget from the bar."""
        if widget in self.right_container.children:
            self.right_container.remove_widget(widget)  # type: ignore
        return widget

    def on_click_research(self, *args: Any):
        """Handle clicking the research label."""
        MessengerGlobal.messenger.send("ui.update.ui.show_research_ui")
