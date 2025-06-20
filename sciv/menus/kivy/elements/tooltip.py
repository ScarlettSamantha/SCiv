from typing import TYPE_CHECKING, Any, List, Self, Tuple
import typing

from direct.task.Task import Task
from kivy.clock import Clock
from kivy.graphics import BorderImage, Color, Line  # type: ignore
from kivy.metrics import dp  # type: ignore
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty  # type: ignore
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label

from gameplay.civilization import T_TranslationOrStr
from helpers.cache import Cache
from helpers.colors import Tuple4f
from managers.i18n import T_TranslationOrStrOrNone
from managers.ui import ui

if TYPE_CHECKING:
    from game import OpenCiv


class TooltipLabel(BoxLayout):
    def __init__(self, text: str, markup: bool = False, image_source: str | None = None, **kwargs: Any):
        super().__init__(orientation="horizontal", spacing=dp(6), padding=(dp(10), dp(6)), **kwargs)  # type: ignore
        self.size_hint = (None, None)  # type: ignore
        self.opacity = 0
        self.bind(minimum_size=self._update_size)  # type: ignore

        with self.canvas.before:
            self.bg_color = Color(0.3, 0.3, 0.3, 0.9)
            self.bg_rect = BorderImage(source="", border=[0, 0, 0, 0])  # type: ignore

        if image_source:
            self.icon = Image(source=image_source, size_hint=(None, None), size=(dp(20), dp(20)))
            self.icon.pos_hint = {"x": 0, "top": 1}
            self.add_widget(self.icon)

        self.label = Label(
            text=text,
            markup=markup,
            color=(1, 1, 1, 1),
            size_hint=(None, None),
            text_size=(None, None),  # type: ignore
        )
        self.label.bind(texture_size=self._update_label_size)  # type: ignore
        self.add_widget(self.label)

        self.bind(pos=self._update_bg, size=self._update_bg)  # type: ignore

    def _update_label_size(self, *_):
        self.label.size = self.label.texture_size  # type: ignore
        self._update_size()  # type: ignore

    def _update_size(self, *_):
        total_width = (  # type: ignore
            sum(c.width for c in self.children) + self.padding[0] * 2 + self.spacing * (len(self.children) - 1)  # type: ignore
        )
        total_height = max(c.height for c in self.children) + self.padding[1] * 2  # type: ignore
        self.size = (total_width, total_height)

    def _update_bg(self, *_):
        self.bg_rect.pos = self.pos  # type: ignore
        self.bg_rect.size = self.size  # type: ignore


class TooltipBehavior:
    tooltip_text: StringProperty = StringProperty("")
    tooltip_visible: BooleanProperty = BooleanProperty(False)
    tooltip_markup: BooleanProperty = BooleanProperty(True)
    tooltip_multiline: BooleanProperty = BooleanProperty(False)
    tooltip_image_source: StringProperty = StringProperty("")
    tooltip_delay = 0.2

    def __init__(self, **kwargs: Any):
        self.base: "OpenCiv" = Cache.get_showbase_instance()
        self.base.taskMgr.add(self._poll_mouse_pos, "_poll_mouse_pos")  # type: ignore
        self.tooltip_label: TooltipLabel | None = None
        self._tooltip_trigger = None
        self._suppress_tooltip = False

        self.register_event_type("on_enter")  # type: ignore
        self.register_event_type("on_leave")  # type: ignore

    def _poll_mouse_pos(self, task: Task) -> int:
        if self.base.mouseWatcherNode.hasMouse():  # type: ignore
            win_size = self.base.win.getSize()  # type: ignore
            px = (self.base.mouseWatcherNode.getMouseX() + 1) * 0.5 * win_size[0]  # type: ignore
            py = (self.base.mouseWatcherNode.getMouseY() + 1) * 0.5 * win_size[1]  # type: ignore
            in_bounds = self.collide_point(*self.to_widget(px, py))  # type: ignore
            if in_bounds:
                self.dispatch("on_enter")  # type: ignore
                if self.tooltip_visible:
                    self.update_tooltip_position(px, py)  # type: ignore
            else:
                self.dispatch("on_leave")  # type: ignore
        return Task.cont

    def update_tooltip_position(self, x: float, y: float):
        if self.tooltip_label:
            parent = ui.get_singleton_instance().get_main_game_ui()
            local_x, local_y = parent.to_widget(x, y)
            offset = 10
            self.tooltip_label.x = local_x + offset
            self.tooltip_label.y = local_y + offset

    def on_enter(self, *args: Any):
        if self._has_disabled_ancestor():
            return
        if not self.tooltip_visible and self.tooltip_text and not self._suppress_tooltip:
            if "<br>" in self.tooltip_text or "\n" in self.tooltip_text:
                self.tooltip_multiline = True
            if self._tooltip_trigger is None:
                self._tooltip_trigger = Clock.schedule_once(self.show_tooltip, self.tooltip_delay)  # type: ignore

    def on_leave(self, *args: Any):
        if self._tooltip_trigger:
            self._tooltip_trigger.cancel()  # type: ignore
            self._tooltip_trigger = None
        self.hide_tooltip()

    def show_tooltip(self, dt: float) -> int:
        if self._has_disabled_ancestor():
            return 0
        image_src = self.tooltip_image_source or getattr(self, "source", "")
        self.tooltip_label = TooltipLabel(
            text=self.tooltip_text,
            markup=True,
            image_source=image_src if image_src else None,
        )
        parent = ui.get_singleton_instance().get_main_game_ui()

        if self.tooltip_label in parent.children:
            parent.remove_widget(self.tooltip_label)
        parent.add_widget(self.tooltip_label)

        if self.base.mouseWatcherNode.hasMouse():  # type: ignore
            win_size = self.base.win.getSize()  # type: ignore
            px = (self.base.mouseWatcherNode.getMouseX() + 1) * 0.5 * win_size[0]  # type: ignore
            py = (self.base.mouseWatcherNode.getMouseY() + 1) * 0.5 * win_size[1]  # type: ignore
            self.update_tooltip_position(px, py)  # type: ignore

        self.tooltip_label.opacity = 1
        self.tooltip_visible = True
        return 0

    def hide_tooltip(self):
        if self.tooltip_label and self.tooltip_visible:
            ui.get_singleton_instance().get_main_game_ui().remove_widget(self.tooltip_label)
        self.tooltip_label = None
        self.tooltip_visible = False

    def _has_disabled_ancestor(self) -> bool:
        widget: Self = self
        while widget:
            if hasattr(widget, "popup_disabled"):  # type: ignore
                return bool(widget.popup_disabled)  # type: ignore
            widget = widget.parent  # type: ignore
        return True


class TooltippedImage(Image, TooltipBehavior):
    tooltip_text = StringProperty("")
    border_size = NumericProperty(1)
    border_color = ListProperty([float, float, float, float])

    def __init__(self, **kwargs: Any):
        border_size = kwargs.pop("border_size", None)
        border_color = kwargs.pop("border_color", None)

        TooltipBehavior.__init__(self, **kwargs)

        if "tooltip_multiline" not in kwargs:
            self.tooltip_multiline = True
            del kwargs["tooltip_multiline"]
        if "tooltip_markup" not in kwargs:
            self.tooltip_markup = False
            del kwargs["tooltip_markup"]
        if "tooltip_image_source" not in kwargs and "source" in kwargs:
            self.tooltip_image_source = kwargs["source"]
            del kwargs["source"]

        if "tooltip_text" in kwargs and isinstance(
            kwargs["tooltip_text"],
            tuple(typing.get_args(T_TranslationOrStr)) + tuple(typing.get_args(T_TranslationOrStrOrNone)),
        ):
            kwargs["tooltip_text"] = str(kwargs["tooltip_text"])

        super().__init__(**kwargs)  # type: ignore

        if border_size is not None:
            self.border_size = border_size
        if border_color is not None:
            self.border_color = border_color

        self.bind(  # type: ignore
            pos=self._update_border,
            size=self._update_border,
            border_color=self._update_border,
            border_size=self._update_border,
        )

        self._update_border()

    def _update_border(self, *args: Any):
        self.canvas.after.clear()  # type: ignore
        with self.canvas.after:  # type: ignore
            color = self.border_color
            Color(r=color[0], g=color[1], b=color[2], a=color[3])  # type: ignore
            Line(rectangle=(self.x, self.y, self.width, self.height), width=self.border_size)  # type: ignore
        self.canvas.ask_update()  # type: ignore

    def on_enter(self, *args: Any):
        ancestor = self._find_tooltip_ancestor()
        if ancestor:
            ancestor._suppress_tooltip = True
            if ancestor.tooltip_visible:
                ancestor.hide_tooltip()
        super().on_enter(*args)

    def on_leave(self, *args: Any):
        ancestor = self._find_tooltip_ancestor()
        if ancestor:
            ancestor._suppress_tooltip = False
        super().on_leave(*args)

    def _find_tooltip_ancestor(self) -> TooltipBehavior | None:
        parent = self.parent
        while parent:
            if isinstance(parent, TooltipBehavior):
                return parent
            parent = parent.parent
        return None


class TooltippedButton(ButtonBehavior, BoxLayout, TooltipBehavior):
    primary_text: str = StringProperty("")  # type: ignore
    image_sources: List[Tuple[str, str]] = ListProperty([])  # type: ignore
    secondary_text: str = StringProperty("")  # type: ignore
    multiline: bool = BooleanProperty(True)  # type: ignore

    background_normal: str = StringProperty("atlas://data/images/defaulttheme/button")  # type: ignore
    background_down: str = StringProperty("atlas://data/images/defaulttheme/button_pressed")  # type: ignore
    border: List[int] = ListProperty([16, 16, 16, 16])  # type: ignore
    background_color: Tuple[float, float, float, float] = ListProperty([1, 1, 1, 1])  # type: ignore

    def __init__(self, **kwargs: Any):
        if "primary_text" in kwargs and isinstance(
            kwargs["primary_text"], (T_TranslationOrStr, T_TranslationOrStrOrNone)
        ):
            kwargs["primary_text"] = str(kwargs["primary_text"])

        if "tooltip_text" in kwargs and isinstance(
            kwargs["tooltip_text"], (T_TranslationOrStr, T_TranslationOrStrOrNone)
        ):
            kwargs["tooltip_text"] = str(kwargs["tooltip_text"])
        ButtonBehavior.__init__(self, **kwargs)  # type: ignore
        BoxLayout.__init__(self, **kwargs)  # type: ignore
        TooltipBehavior.__init__(self, tooltip_markup=True, **kwargs)

        with self.canvas.before:
            self._bg_color_inst = Color(rgba=self.background_color)  # type: ignore
            self._bg_image = BorderImage(  # type: ignore
                source=self.background_normal, border=self.border, pos=self.pos, size=self.size
            )

        self.bind(
            pos=self._update_bg,
            size=self._update_bg,
            background_color=self._update_bg_color,  # type: ignore
            background_normal=self._update_bg_source,
            background_down=self._update_bg_source,
            border=self._update_bg_border,  # type: ignore
            state=self._update_bg_source,
        )

        self.orientation = "vertical"
        self.padding = dp(4)
        self.spacing = dp(4)
        self.height = dp(64)
        self.width = dp(200)

        self._title_lbl = Label(text=self.primary_text, size_hint_y=None)
        self._title_lbl.bind(texture_size=self._update_label_height)  # type: ignore
        self.add_widget(self._title_lbl)

        self._second_line = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(24),
            spacing=dp(2),  # type: ignore
            padding=(0, 0),
        )
        self.add_widget(self._second_line)

        self.bind(
            primary_text=self._on_primary_text,  # type: ignore
            image_sources=self._refresh_second_line,
            secondary_text=self._refresh_second_line,
        )
        self._refresh_second_line()

    def _update_bg(self, *args: Any):
        self._bg_image.pos = self.pos  # type: ignore
        self._bg_image.size = self.size  # type: ignore

    def _update_bg_color(self, _, val: Tuple4f):
        self._bg_color_inst.rgba = val

    def _update_bg_source(self, *args: Any):
        src = self.background_down if self.state == "down" else self.background_normal
        self._bg_image.source = src  # type: ignore

    def _update_bg_border(self, _, val: List[int]):
        self._bg_image.border = val  # type: ignore

    def _update_label_height(self, lbl: Label, sz: tuple[int, int]) -> None:
        lbl.height = sz[1]

    def _on_primary_text(self, _, new: str):
        self._title_lbl.text = new

    def _refresh_second_line(self, *args: Any):
        self._second_line.clear_widgets()
        if not self.multiline:
            return

        icon_size = dp(24)

        for src, tip in self.image_sources:
            img = TooltippedImage(
                source=src,
                tooltip_text=tip,
                tooltip_markup=False,
                tooltip_multiline=True,
                tooltip_image_source=src,
                size_hint=(None, None),
                size=(icon_size, icon_size),
                allow_stretch=True,
                keep_ratio=True,
            )
            self._second_line.add_widget(img)

        if self.secondary_text:
            lbl = Label(
                text=self.secondary_text,
                valign="middle",
                halign="left",
                size_hint=(None, None),
            )
            lbl.text_size = (None, icon_size)  # type: ignore
            lbl.height = icon_size
            lbl.padding = (dp(4), 0)  # type: ignore

            def _update_width(_lbl, size):  # type: ignore
                lbl.width = size[0]

            lbl.bind(texture_size=_update_width)  # type: ignore
            self._second_line.add_widget(lbl)
