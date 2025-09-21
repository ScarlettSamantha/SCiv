import datetime
import logging
from typing import TYPE_CHECKING, Any, Dict, Tuple, cast

from helpers.colors import Colors, Tuple4f
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from menus.kivy.elements.clipping import ClippingScrollList
from menus.kivy.elements.list_item import ListItem
from menus.kivy.parts.popup import BasePopup

if TYPE_CHECKING:
    from managers.log import UILogHandler


class LogPopup(BasePopup):
    ALL_MARKER: str = "ALL"
    severity_filter: StringProperty = StringProperty(ALL_MARKER)

    def __init__(self, handler: "UILogHandler", *args: Any, **kwargs: Dict[str, Any]):
        layout = BoxLayout(orientation="vertical")
        super().__init__(content=layout, *args, **kwargs)  # type: ignore
        self.index: int = 0
        self.size_hunt = (0.8, 0.8)

        self.handler = handler
        handler.on_log = self.on_new_log

        # severity filter spinner
        self.spinner = Spinner(
            text=self.ALL_MARKER,
            values=[self.ALL_MARKER] + list(logging._nameToLevel.keys()),  # type: ignore
            size_hint=(1, None),
            height=dp(40),
        )
        self.spinner.bind(text=self.on_filter)
        layout.add_widget(self.spinner)

        self.scroll = ClippingScrollList(cols=1, size_hint=(1, 1))
        layout.add_widget(self.scroll)

        Clock.schedule_once(lambda dt: self.load_all(), 0)  # type: ignore

    def on_new_log(self, _datetime: datetime.datetime, level: str, msg: str) -> None:
        pass

    def load_all(self) -> None:
        self.scroll.clear_widgets()
        self.index = 0
        self.severity_filter = self.spinner.text

        for ts, level, msg in self.handler.records:
            if self.passes_filter(level):
                dt = datetime.datetime.fromtimestamp(ts)
                self.index += 1
                if self.index % 2 == 0:
                    background_color: Tuple[float, ...] = Colors.DARK_GRAY
                else:
                    background_color = Colors.LIGHT_GRAY

                self._add_line(dt, msg, level, background_color)
        Clock.schedule_once(lambda dt: self.scroll.scroll_to_bottom(), 0)  # type: ignore

    def on_filter(self, spinner: Spinner, text: str) -> None:
        self.severity_filter = text
        self.load_all()

    def passes_filter(self, level: str) -> bool:
        return level == self.severity_filter or self.severity_filter == self.ALL_MARKER

    def _add_line(
        self, timestamp: datetime.datetime, msg: str, level: str, background_color: Tuple[float, ...] = Colors.BLACK
    ) -> None:
        color_value = self.get_color(level)
        color_str: str = Colors.to_hex(color_value)
        item = ListItem(
            text=f"[{timestamp.strftime('%H:%M:%S')}][color={color_str}][{level}][/color]: {msg}",
            background_color=cast(Tuple4f, background_color),
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="middle",
            markup=True,
        )
        self.scroll.add_widget(item)

        Clock.schedule_once(lambda dt: self.scroll.scroll_to_bottom(), 0)  # type: ignore

    def get_color(self, level: str) -> Tuple[float, float, float, float]:
        mapping = {
            "DEBUG": Colors.GREEN,
            "INFO": Colors.TIEL,
            "WARNING": Colors.YELLOW,
            "ERROR": Colors.ORANGE,
            "CRITICAL": Colors.RED,
        }
        return mapping.get(level, Colors.MAGENTA)

    def scroll_to_start(self) -> None:
        self.scroll.scroll_to_top()

    def clear_lines(self) -> None:
        self.scroll.clear_widgets()
        self.index = 0

    def open(self, *args: Any, **kwargs: Any) -> None:
        self.handler.on_log = self.on_new_log
        self.load_all()
        self.scroll_to_start()
        self.spinner.text = self.ALL_MARKER
        return super().open(*args, **kwargs)

    def done(self, *args: Any, **kwargs: Any) -> None:
        self.clear_lines()
        self.handler.on_log = None
        super().done(*args, **kwargs)
