from functools import partial
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Sequence, Tuple, Type, TypeIs, cast

from gameplay.improvement import Improvement
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from system.actions import Action

from gameplay.unit import BaseUnitAction

if TYPE_CHECKING:
    from gameplay.unit import Unit

    from sciv.game import OpenCiv


class PanelButton(Button):
    corner_pad = NumericProperty(2)

    bg_color = ListProperty([0.2, 0.2, 0.2, 0.75])
    bg_color_down = ListProperty([0.0, 0.0, 0.0, 0.95])
    text_color = ListProperty([0.92, 0.92, 0.92, 1.0])
    disabled_alpha = NumericProperty(0.45)

    highlight = BooleanProperty(False)  # type: ignore
    highlight_color = ListProperty([1.0, 1.0, 1.0, 1.0])
    highlight_width = NumericProperty(2)

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
        self.border = (0.2, 0.2, 0.2, 1)

        self.background_color = (0, 0, 0, 0)
        self.highlight: bool = True

        self.color = self.text_color[:]

        with self.canvas.before:  # type: ignore
            self._c_bg = Color(*self.bg_color)  # type: ignore
            self._rect_bg = Rectangle(pos=self.pos, size=self.size)  # type: ignore

        with self.canvas.after:  # type: ignore
            self._c_hl = Color(*self.highlight_color)  # type: ignore
            self._line_hl = Line(rectangle=(0, 0, 0, 0), width=float(self.highlight_width))  # type: ignore

        self.set_border_color(list(self.border))

        self.bind(
            pos=self._recompute_geometry,
            size=self._recompute_geometry,
            corner_pad=lambda *_: self._recompute_geometry(),
            highlight_width=lambda *_: self._recompute_geometry(),
            bg_color=lambda *_: self._apply_state_colors(),
            bg_color_down=lambda *_: self._apply_state_colors(),
            text_color=lambda *_: setattr(self, "color", self.text_color[:]),
            state=lambda *_: self._apply_state_colors(),
            disabled=lambda *_: self._apply_state_colors(),
            highlight=lambda *_: self._apply_highlight(),
            highlight_color=lambda *_: self._apply_highlight(),
        )

        self._recompute_geometry()
        self._apply_state_colors()
        self._apply_highlight()

    def _recompute_geometry(self, *_: Any) -> None:
        x, y = cast(Tuple[float | int, float | int], self.pos)
        w, h = cast(Tuple[float | int, float | int], self.size)
        pad = float(self.corner_pad)
        self._rect_bg.pos = (x + pad, y + pad)  # type: ignore
        self._rect_bg.size = (w - 2 * pad, h - 2 * pad)  # type: ignore

        hw = float(self.highlight_width) * 0.5
        self._line_hl.rectangle = (x + hw, y + hw, w - 2 * hw, h - 2 * hw)  # type: ignore
        self._line_hl.width = float(self.highlight_width)  # type: ignore

    def _apply_state_colors(self, *_: Any) -> None:
        base_bg = list(self.bg_color_down if self.state == "down" else self.bg_color)  # type: ignore
        alpha: float = base_bg[3]
        if self.disabled:
            bg = [base_bg[0], base_bg[1], base_bg[2], alpha * self.disabled_alpha]
            txt = [
                self.text_color[0],
                self.text_color[1],
                self.text_color[2],
                self.text_color[3] * self.disabled_alpha,
            ]
        else:
            bg = base_bg[:]
            txt = list(self.text_color)
        self._set_color(self._c_bg, bg)
        self.color = txt  # type: ignore

    def _apply_highlight(self, *_: Any) -> None:
        col = list(self.highlight_color)
        if not self.highlight:
            col[3] = 0.0  # hide by zeroing alpha
        self._set_color(self._c_hl, col)

    # Convenience API
    def toggle_highlight(self, on: bool | None = None) -> None:
        self.highlight = (not self.highlight) if on is None else bool(on)

    @staticmethod
    def _set_color(instr: Color, rgba: Sequence[float]) -> None:
        instr.rgba = rgba  # type: ignore[attr-defined]

    def _recompute_rect(self, *_: Any) -> None:
        x, y = cast(Tuple[float | int, float | int], self.pos)
        w, h = cast(Tuple[float | int, float | int], self.size)
        pad = float(self.corner_pad)
        self._rect_bg.pos = (x + pad, y + pad)  # type: ignore
        self._rect_bg.size = (w - 2 * pad, h - 2 * pad)  # type: ignore

    def set_border_color(self, color: Sequence[float]) -> None:
        self.highlight_color = color
        self._apply_highlight()


class PlayerActionBar(BoxLayout):
    def __init__(self, base: "OpenCiv", *args: Any, **kwargs: Any):
        super().__init__(**kwargs)
        self.base = base
        self.border = (0, 0, 0, 0)
        self.background_image = ""
        self.frame: Optional[GridLayout] = None
        self.prepare_action: Optional[Callable[..., Any]] = None
        self.prepare_build_action: Optional[Callable[..., Any]] = None

        self.current_unit: Optional["Unit"] = None
        self.action_preparer: Callable[..., Any] | None = None
        self.build_action_preparer: Callable[..., Any] | None = None
        self.current_action: Optional[Action] = None

    def build(self) -> GridLayout:
        window_size_x, window_size_y = self.base.win.getXSize(), self.base.win.getYSize()  # type: ignore
        self.frame = GridLayout(
            orientation="lr-tb",
            size_hint=(None, None),
            width=1150,
            height=dp(100),
            padding=(dp(15), dp(12), dp(10), dp(15)),
            spacing=dp(10),
            pos=(dp((window_size_x // 2) - (1150 / 2)), dp(10)),
            cols=12,
            rows=1,
        )
        with self.frame.canvas.before:
            self._bg_color = Color(0.1, 0.1, 0.1, 0.7)  # Transparent black background
            self._bg_rect = Rectangle(pos=self.frame.pos, size=self.frame.size)  # type: ignore

        self.frame.bind(
            pos=lambda instance, value: setattr(self._bg_rect, "pos", value),
            size=lambda instance, value: setattr(self._bg_rect, "size", value),
        )
        return self.frame

    def fire_event(self, *args: Any, **kwargs: Any) -> None:
        if self.prepare_action is not None:
            self.prepare_action(*args, **kwargs)
        self.current_action = kwargs.get("action", None)
        self.clear_buttons()
        self._generate_buttons()

    def _generate_buttons(self) -> None:
        if self.current_unit is None or self.prepare_action is None or self.prepare_build_action is None:
            return

        actions: List[BaseUnitAction] = self.current_unit.get_actions()
        for action in actions:
            btn = PanelButton(text=str(action.name))
            if action.is_disabled or (
                action.has_movement_point_left_requirement
                and self.current_unit.moves_left < action.movement_point_left_requirement
            ):  # type: ignore
                btn.disabled = True
            if self.current_action is not None and action == self.current_action and not self.current_action.has_run():
                btn.set_border_color([1.0, 1.0, 1.0, 1.0])
                btn.highlight = True
            btn.bind(on_press=partial(self.fire_event, action=action, executor=self.current_unit))  # type: ignore
            self.add_button(btn)

        if self.current_unit.can_build is True:
            improvements: List[Type[Improvement]] = self.current_unit.get_tile().get_buildable_improvements()
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
                    and not self.current_unit.get_tile().improvements().has(_improvement)
                    and visible_condition_check
                ):
                    btn = PanelButton(text=str(_improvement.name))
                    btn.disabled = (
                        not self.current_unit.can_build
                        or self.current_unit.get_tile().owner != self.current_unit.owner
                        or condition_check is False
                    )
                    btn.bind(  # type: ignore
                        on_press=lambda x, improvement=_improvement: self.prepare_build_action(
                            improvement, self.current_unit
                        )  # type: ignore
                    )
                    self.add_button(btn)

    def generate(
        self,
        unit: "Unit",
        action_preparer: Callable[..., Any],
        build_action_preparer: Callable[..., Any],
        current_action: Optional[Action] = None,
    ) -> None:
        self.current_unit = unit
        self.prepare_action = action_preparer
        self.prepare_build_action = build_action_preparer
        self.current_action = current_action
        self.clear_buttons()
        self._generate_buttons()

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
