import typing
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from gameplay.civilization import T_TranslationOrStr
from helpers.cache import Cache
from helpers.colors import Tuple4f
from kivy.clock import Clock
from kivy.graphics import BorderImage, Color, Line  # type: ignore
from kivy.metrics import dp  # type: ignore
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty  # type: ignore
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from managers.i18n import T_TranslationOrStrOrNone
from managers.ui import ui
from system.tooltip_poller import TooltipPoller

if TYPE_CHECKING:
    from game import OpenCiv


class TooltipSet(Enum):
    TECHNOLOGY_TREE = "technology_tree"
    CIVICS_TREE = "civics_tree"


class TooltipSets:
    sets: Dict[TooltipSet, bool] = {
        TooltipSet.TECHNOLOGY_TREE: True,
        TooltipSet.CIVICS_TREE: True,
    }

    @classmethod
    def is_enabled(cls, key: TooltipSet) -> bool:
        return cls.sets.get(key, True)

    @classmethod
    def set_enabled(cls, key: TooltipSet, enabled: bool):
        cls.sets[key] = enabled

    @classmethod
    def toggle(cls, key: TooltipSet):
        cls.sets[key] = not cls.sets.get(key, True)

    @classmethod
    def disable_all(cls):
        for key in cls.sets.keys():
            cls.sets[key] = False

    @classmethod
    def enable_all(cls):
        for key in cls.sets.keys():
            cls.sets[key] = True

    @classmethod
    def clear(cls):
        cls.sets = {}

    @classmethod
    def get_all(cls) -> Dict[TooltipSet, bool]:
        return cls.sets

    @classmethod
    def enable(cls, key: TooltipSet):
        cls.sets[key] = True

    @classmethod
    def disable(cls, key: TooltipSet):
        cls.sets[key] = False


class TooltipLabel(BoxLayout):
    def __init__(self, text: str, markup: bool = True, image_source: str | None | Image = None, **kwargs: Any):
        super().__init__(orientation="horizontal", spacing=dp(6), padding=(dp(10), dp(6)), **kwargs)  # type: ignore
        self.size_hint = (None, None)  # type: ignore
        self.opacity = 0
        self.bind(minimum_size=self._update_size)  # type: ignore

        with self.canvas.before:
            self.bg_color = Color(0.3, 0.3, 0.3, 0.9)
            self.bg_rect = BorderImage(source="", border=[0, 0, 0, 0])  # type: ignore

        if image_source:
            if isinstance(image_source, str):
                self.icon = Image(source=image_source, size_hint=(None, None), size=(dp(20), dp(20)))
            else:
                self.icon = image_source
            self.icon.pos_hint = {"x": 0, "top": 1}
            self.add_widget(self.icon)

        self.label = Label(
            text=text,
            markup=True,
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
    tooltip_anchor_x: StringProperty = StringProperty("auto")  # 'auto' | 'left' | 'right'
    tooltip_anchor_y: StringProperty = StringProperty("auto")  # 'auto' | 'top' | 'bottom'
    tooltip_margin: NumericProperty = NumericProperty(10)  # type:ignore
    tooltip_delay = 0.2

    def __init__(self, **kwargs: Any):
        self.base: "OpenCiv" = Cache.get_showbase_instance()
        self.tooltip_label: TooltipLabel | None = None
        self._tooltip_trigger = None
        self._suppress_tooltip = False
        self.tooltip_set: TooltipSet | None = kwargs.pop("tooltip_set", None)

        self.hovered: bool = False

        TooltipPoller.instance().register(self)

        self.bind(tooltip_visible=self._on_tooltip_visible)  # type: ignore

        if hasattr(self, "register_event_type"):
            self.register_event_type("on_enter")  # type: ignore
            self.register_event_type("on_leave")  # type: ignore

        if hasattr(self, "bind"):
            try:
                self.bind(opacity=lambda *_: self.maybe_hide_if_not_pollworthy())  # type: ignore
                self.bind(parent=lambda *_: self.maybe_hide_if_not_pollworthy())  # type: ignore
                self.bind(size=lambda *_: self.maybe_hide_if_not_pollworthy())  # type: ignore
                self.bind(pos=lambda *_: self.maybe_hide_if_not_pollworthy())  # type: ignore
                self.bind(tooltip_text=lambda *_: self.maybe_hide_if_not_pollworthy())  # type: ignore
            except Exception:
                pass  # nosec: B110

    def _on_tooltip_visible(self, instance: "TooltipBehavior", value: bool):
        if self.tooltip_set and not TooltipSets.is_enabled(self.tooltip_set):
            if value:
                self.hide_tooltip()
            self._suppress_tooltip = True
        else:
            self._suppress_tooltip = False

    def show_tooltip(self, *args: Any) -> None:
        if self.tooltip_visible or self._suppress_tooltip:
            return
        if not (self.tooltip_text or getattr(self, "tooltip_image_source", "")):
            return

        img_src = self.tooltip_image_source if self.tooltip_image_source else None
        self.tooltip_label = TooltipLabel(
            text=self.tooltip_text,
            markup=True,
            image_source=img_src,
            size_hint=(None, None),
        )
        if self.tooltip_multiline:
            self.tooltip_label.label.text_size = (dp(300), None)
            self.tooltip_label.label.halign = "left"

        parent = ui.get_singleton_instance().get_main_game_ui()
        if self.tooltip_label in parent.children:
            parent.remove_widget(self.tooltip_label)
        parent.add_widget(self.tooltip_label)

        if self.base.mouseWatcherNode.hasMouse():  # type: ignore
            win_size = self.base.win.getSize()  # type: ignore
            px = (self.base.mouseWatcherNode.getMouseX() + 1) * 0.5 * win_size[0]  # type: ignore
            py = (self.base.mouseWatcherNode.getMouseY() + 1) * 0.5 * win_size[1]  # type: ignore
            self.update_tooltip_position(px, py)

        self.tooltip_label.opacity = 1
        self.tooltip_visible = True

    def hide_tooltip(self) -> None:
        if not self.tooltip_visible:
            return
        if self.tooltip_label:
            self.tooltip_label.opacity = 0
            if self.tooltip_label.parent:
                self.tooltip_label.parent.remove_widget(self.tooltip_label)
            self.tooltip_label = None
        self.tooltip_visible = False

    def handle_global_mouse(self, px: float, py: float) -> None:
        in_bounds = self.collide_point(*self.to_widget(px, py))  # type: ignore

        if in_bounds and not self.hovered:
            self.hovered = True
            self.dispatch("on_enter")  # type: ignore
        elif not in_bounds and self.hovered:
            self.hovered = False
            self.dispatch("on_leave")  # type: ignore

        if in_bounds and self.tooltip_visible:
            self.update_tooltip_position(px, py)

    def update_tooltip_position(self, x: float, y: float) -> None:
        if not self.tooltip_label:
            return

        parent = ui.get_singleton_instance().get_main_game_ui()
        local_x, local_y = parent.to_widget(x, y)

        try:
            self.tooltip_label.label.texture_update()  # type: ignore
        except Exception:
            pass  # nosec: B110
        self.tooltip_label._update_size()  # type: ignore

        tw, th = self.tooltip_label.size  # type: ignore
        pw, ph = parent.width, parent.height
        margin = dp(self.tooltip_margin)  # type: ignore

        tx: int = int(local_x + margin if self.tooltip_anchor_x in ("left", "auto") else local_x - tw - margin)  # type: ignore
        ty: int = int(local_y + margin if self.tooltip_anchor_y in ("bottom", "auto") else local_y - th - margin)  # type: ignore

        if tx + tw > pw:
            tx = int(local_x - tw - margin)  # type: ignore
        if tx < margin:
            tx = margin
        if ty + th > ph:
            ty = int(local_y - th - margin)  # type: ignore
        if ty < margin:
            ty = margin

        self.tooltip_label.pos = (tx, ty)  # type: ignore

    def should_poll(self) -> bool:
        if self._suppress_tooltip:
            return False
        if not self.tooltip_text and not getattr(self, "tooltip_image_source", ""):
            return False
        return True

    def maybe_hide_if_not_pollworthy(self) -> None:
        if not self.should_poll():
            if self.tooltip_visible:
                self.hide_tooltip()
            self.hovered = False

    def on_enter(self, *args: Any):
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

    def destroy(self) -> None:
        if self._tooltip_trigger:
            try:
                self._tooltip_trigger.cancel()  # type: ignore
            except Exception:
                pass
            self._tooltip_trigger = None
        TooltipPoller.instance().unregister(self)
        self.hide_tooltip()


class TooltippedImage(Image, TooltipBehavior):
    tooltip_text = StringProperty("")
    border_size = NumericProperty(1)
    border_color = ListProperty([float, float, float, float])

    def __init__(self, **kwargs: Any):
        border_size = kwargs.pop("border_size", None)
        border_color = kwargs.pop("border_color", None)

        self.tooltip_multiline = bool(kwargs.pop("tooltip_multiline", True))
        self.tooltip_markup = bool(kwargs.pop("tooltip_markup", False))
        if "tooltip_image_source" not in kwargs and "source" in kwargs:
            self.tooltip_image_source = kwargs["source"]

        if "tooltip_text" in kwargs and isinstance(
            kwargs["tooltip_text"],
            tuple(typing.get_args(T_TranslationOrStr)) + tuple(typing.get_args(T_TranslationOrStrOrNone)),
        ):
            kwargs["tooltip_text"] = str(kwargs["tooltip_text"])

        super().__init__(**kwargs)  # type: ignore
        TooltipBehavior.__init__(self)

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
        if "primary_text" in kwargs:
            primary_types = tuple(
                t for union in (T_TranslationOrStr, T_TranslationOrStrOrNone) for t in typing.get_args(union)
            )
            if isinstance(kwargs["primary_text"], primary_types):
                kwargs["primary_text"] = str(kwargs["primary_text"])

        if "tooltip_text" in kwargs:
            tooltip_types = tuple(
                t for union in (T_TranslationOrStr, T_TranslationOrStrOrNone) for t in typing.get_args(union)
            )
            if isinstance(kwargs["tooltip_text"], tooltip_types):
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

        self._title_lbl = Label(text=self.primary_text, size_hint_y=None, markup=True)
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
                tooltip_markup=True,
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
                markup=True,
                size_hint=(None, None),
            )
            lbl.text_size = (None, icon_size)  # type: ignore
            lbl.height = icon_size
            lbl.padding = (dp(4), 0)  # type: ignore

            def _update_width(_lbl, size):  # type: ignore
                lbl.width = size[0]

            lbl.bind(texture_size=_update_width)  # type: ignore
            self._second_line.add_widget(lbl)
