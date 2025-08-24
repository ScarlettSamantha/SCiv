from functools import partial
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Tuple, Type, TypeIs, cast

from direct.showbase.DirectObject import DirectObject
from gameplay.improvement import Improvement
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout

from sciv.system.actions import Action

if TYPE_CHECKING:
    from gameplay.unit import Unit


class PanelButton(Button):
    border_px = NumericProperty(2)
    corner_pad = NumericProperty(2)

    border_color = ListProperty([0.0, 0.0, 0.0, 1.0])  # black
    bg_color = ListProperty([0.10, 0.10, 0.10, 1.0])  # dark gray
    bg_color_down = ListProperty([0.22, 0.22, 0.22, 1.0])  # slightly lighter when pressed
    text_color = ListProperty([0.92, 0.92, 0.92, 1.0])  # off-white
    disabled_alpha = NumericProperty(0.45)

    def __init__(self, **kwargs: Any):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("width", dp(100))
        kwargs.setdefault("height", dp(75))
        kwargs.setdefault("shorten", True)
        kwargs.setdefault("shorten_from", "right")
        kwargs.setdefault("halign", "center")
        kwargs.setdefault("valign", "bottom")
        super().__init__(**kwargs)

        self.background_normal = ""
        self.background_down = ""
        self.background_disabled_normal = ""
        self.background_disabled_down = ""
        self.border = (0, 0, 0, 0)
        self.background_color = (0, 0, 0, 0)
        self.color = self.text_color[:]

        with self.canvas.before:  # type: ignore
            self._c_border = Color(*self.border_color)  # type: ignore
            self._rect_border = Rectangle(pos=self.pos, size=self.size)  # type: ignore
            self._c_bg = Color(*self.bg_color)  # type: ignore
            self._rect_bg = Rectangle(pos=self.pos, size=self.size)  # type: ignore

        self.bind(
            pos=self._recompute_rects,
            size=self._recompute_rects,
            border_px=lambda *_: self._recompute_rects(),
            corner_pad=lambda *_: self._recompute_rects(),
            border_color=lambda *_: self._set_color(self._c_border, self.border_color),
            bg_color=lambda *_: self._apply_state_colors(),
            bg_color_down=lambda *_: self._apply_state_colors(),
            text_color=lambda *_: setattr(self, "color", self.text_color[:]),
            state=lambda *_: self._apply_state_colors(),
            disabled=lambda *_: self._apply_state_colors(),
        )

        self._recompute_rects()
        self._apply_state_colors()

    @staticmethod
    def _set_color(instr: Color, rgba: List[float]) -> None:
        instr.rgba = rgba  # type: ignore[attr-defined]

    def _recompute_rects(self, *_: Any) -> None:
        x, y = cast(Tuple[float | int, float | int], self.pos)
        w, h = cast(Tuple[float | int, float | int], self.size)
        b = float(self.border_px)
        pad = float(self.corner_pad)

        self._rect_border.pos = (x, y)  # type: ignore
        self._rect_border.size = (w, h)  # type: ignore

        self._rect_bg.pos = (x + b + pad, y + b + pad)  # type: ignore
        self._rect_bg.size = (w - 2 * (b + pad), h - 2 * (b + pad))  # type: ignore

    def _apply_state_colors(self, *_: Any) -> None:
        base_bg: List[float] = self.bg_color_down if self.state == "down" else self.bg_color  # type: ignore
        alpha: float = base_bg[3]

        if self.disabled:
            bg: List[float] = [base_bg[0], base_bg[1], base_bg[2], alpha * self.disabled_alpha]
            txt: List[float] = [
                self.text_color[0],
                self.text_color[1],
                self.text_color[2],
                self.text_color[3] * self.disabled_alpha,
            ]
        else:
            bg = base_bg[:]
            txt = self.text_color[:]

        self._set_color(self._c_bg, bg)
        self.color = txt  # type: ignore


class ActionBar(BoxLayout, DirectObject):
    def __init__(self, *args: Any, **kwargs: Any):
        self.background_color = (0, 0, 0, 1)
        self.border = (1, 1, 1, 1)
        self.background_image = ""
        super().__init__(*args, **kwargs)  # type: ignore
        self.frame: Optional[GridLayout] = None
        self.prepare_action: Optional[Callable[..., Any]] = None
        self.prepare_build_action: Optional[Callable[..., Any]] = None

    def build(self) -> GridLayout:
        self.frame = GridLayout(  # noqa: F821
            orientation="lr-tb",
            size_hint=(None, None),
            width=1000,
            height=dp(85),
            spacing=dp(10),
            pos=(dp(800), dp(0)),
            cols=12,
            rows=1,
        )
        return self.frame

    def generate(
        self,
        unit: "Unit",
        action_preparer: Callable[..., Any],
        build_action_preparer: Callable[..., Any],
    ) -> None:
        actions: List[Action] = unit.get_actions()
        for action in actions:
            btn = PanelButton(text=str(action.name))
            if action.is_disabled:
                btn.disabled = True
            btn.bind(on_press=partial(action_preparer, action=action, executor=unit))  # type: ignore
            self.add_button(btn)

        if unit.can_build is True:
            improvements: List[Type[Improvement]] = unit.get_tile().get_buildable_improvements()
            for _improvement in improvements:
                condition_check: TypeIs[Callable[..., object]] | bool = (
                    isinstance(_improvement.placeable_on_condition, bool)
                    and _improvement.placeable_on_condition is True
                ) or (callable(_improvement.placeable_on_condition) and _improvement.placeable_on_condition() is True)

                visible_condition_check: TypeIs[Callable[..., object]] | bool = (
                    isinstance(_improvement.visible_on_condition, bool) and _improvement.visible_on_condition is True
                ) or (callable(_improvement.visible_on_condition) and _improvement.visible_on_condition() is True)

                if (
                    _improvement.placeable_on_tiles is True
                    and not unit.get_tile().improvements().has(_improvement)
                    and visible_condition_check
                ):
                    btn = PanelButton(text=str(_improvement.name))
                    btn.disabled = not unit.can_build or unit.get_tile().owner != unit.owner or condition_check is False
                    btn.bind(  # type: ignore
                        on_press=lambda x, improvement=_improvement: self.prepare_build_action(improvement, unit)  # type: ignore
                    )
                    self.add_button(btn)

    def get_frame(self) -> GridLayout:
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
