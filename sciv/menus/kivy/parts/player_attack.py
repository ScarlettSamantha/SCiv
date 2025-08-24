from math import sin
from typing import TYPE_CHECKING, Any, List, Optional, Tuple, cast

from direct.showbase.DirectObject import DirectObject
from helpers.colors import Colors
from helpers.paths import PathsHelper
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from managers.assets import AssetManager
from managers.i18n import t_

if TYPE_CHECKING:
    from gameplay.unit import Unit as UnitType


from kivy.properties import ListProperty, NumericProperty, OptionProperty


class _PredictedLossHealthBar(Widget):
    current_value = NumericProperty(10.0)
    max_value = NumericProperty(10.0)
    predicted_loss = NumericProperty(0.0)

    direction = OptionProperty("ltr", options=("ltr", "rtl"))  # type: ignore
    mode = OptionProperty("segment", options=("segment", "overlay"))  # type: ignore

    bg_color = ListProperty([0.10, 0.10, 0.10, 1.0])
    fill_color = ListProperty([0.20, 0.80, 0.25, 1.0])
    border_color = ListProperty([0.0, 0.0, 0.0, 1.0])
    loss_color = ListProperty([0.95, 0.15, 0.12, 1.0])

    loss_alpha_base = NumericProperty(0.35)
    loss_alpha_var = NumericProperty(0.15)

    border_px = NumericProperty(2)
    corner_pad = NumericProperty(2)

    _glow_alpha: float = 0.35

    _rect_border: Rectangle | None = None
    _rect_bg: Rectangle | None = None
    _rect_fill: Rectangle | None = None
    _rect_loss: Rectangle | None = None

    def __init__(self, **kwargs: Any):
        direction_kw = kwargs.pop("direction", None)
        super().__init__(**kwargs)

        with self.canvas:  # type: ignore
            self._c_border = Color(*self.border_color)  # type: ignore
            self._rect_border = Rectangle(pos=self.pos, size=self.size)  # type: ignore

            self._c_bg = Color(*self.bg_color)  # type: ignore
            self._rect_bg = Rectangle(pos=self.pos, size=self.size)  # type: ignore

            self._c_fill = Color(*self.fill_color)  # type: ignore
            self._rect_fill = Rectangle(pos=self.pos, size=(0, 0))  # type: ignore

            lc: List[float] = self.loss_color[:3] + [self._glow_alpha]
            self._c_loss = Color(*lc)  # type: ignore
            self._rect_loss = Rectangle(pos=self.pos, size=(0, 0))  # type: ignore

        if direction_kw is not None:
            self.direction = str(direction_kw)

        self.bind(
            pos=self._recompute,
            size=self._recompute,
            current_value=self._recompute,
            max_value=self._recompute,
            predicted_loss=self._recompute,
            mode=self._recompute,
            bg_color=lambda *_: self._set_color(self._c_bg, self.bg_color),
            fill_color=lambda *_: self._set_color(self._c_fill, self.fill_color),
            border_color=lambda *_: self._set_color(self._c_border, self.border_color),
            loss_color=lambda *_: self._set_color(self._c_loss, self.loss_color[:3] + [self._glow_alpha]),
        )

    def set_glow_alpha(self, a: float) -> None:
        a = max(0.0, min(1.0, a))
        self._glow_alpha = a
        self._set_color(self._c_loss, self.loss_color[:3] + [a])

    @staticmethod
    def _set_color(color_instr: Color, rgba: list[float]) -> None:
        color_instr.rgba = rgba  # type: ignore[attr-defined]

    def _inner_rect(self) -> Tuple[float, float, float, float]:
        x, y = cast(Tuple[float, float], self.pos)
        w, h = cast(Tuple[float, float], self.size)
        b = float(self.border_px)

        if self._rect_border:
            self._rect_border.pos = (x, y)  # type: ignore
            self._rect_border.size = (w, h)  # type: ignore
        if self._rect_bg:
            self._rect_bg.pos = (x + b, y + b)  # type: ignore
            self._rect_bg.size = (w - 2 * b, h - 2 * b)  # type: ignore

        return (
            x + b + float(self.corner_pad),
            y + b + float(self.corner_pad),
            w - 2 * (b + float(self.corner_pad)),
            h - 2 * (b + float(self.corner_pad)),
        )

    def _recompute(self, *_: Any) -> None:
        if self.max_value <= 0:
            return

        x, y, w, h = self._inner_rect()

        cur = max(0.0, min(self.current_value, self.max_value))
        loss = max(0.0, min(self.predicted_loss, cur))
        kept = max(0.0, cur - loss)

        kept_w = (kept / self.max_value) * w
        loss_w = (loss / self.max_value) * w
        fill_w = (cur / self.max_value) * w

        if self.mode == "segment":
            if self.direction == "ltr":
                fill_pos = (x, y)
                loss_x = x + kept_w
            else:
                fill_pos = (x + (w - kept_w), y)
                loss_x = fill_pos[0] - loss_w

            if self._rect_fill:
                self._rect_fill.pos = fill_pos  # type: ignore
                self._rect_fill.size = (kept_w, h)  # type: ignore

            if self._rect_loss:
                if loss_w > 0:
                    self._rect_loss.pos = (loss_x, y)  # type: ignore
                    self._rect_loss.size = (loss_w, h)  # type: ignore
                else:
                    self._rect_loss.size = (0, 0)

        else:  # overlay
            if self.direction == "ltr":
                fill_pos = (x, y)
                loss_x = x + fill_w - loss_w
            else:
                fill_pos = (x + (w - fill_w), y)
                loss_x = x + (w - fill_w)

            if self._rect_fill:
                self._rect_fill.pos = fill_pos  # type: ignore
                self._rect_fill.size = (fill_w, h)  # type: ignore

            if self._rect_loss:
                if loss_w > 0 and fill_w > 0:
                    self._rect_loss.pos = (loss_x, y)  # type: ignore
                    self._rect_loss.size = (loss_w, h)  # type: ignore
                else:
                    self._rect_loss.size = (0, 0)


class _UnitSide(BoxLayout):
    direction: str = "ltr"
    name_text: str = ""
    bar_height: int = 32

    def __init__(self, direction: str = "ltr", **kwargs: Any):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("spacing", dp(6))
        kwargs.setdefault("padding", (0, 0, 0, 0))
        super().__init__(**kwargs)
        self.direction = direction

        row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint=(1, None), height=dp(64))
        self.add_widget(row)

        self.icon = Image(size_hint=(None, None), size=(dp(64), dp(64)))
        self._spacer = Widget(size_hint_x=None, width=dp(6))

        bar_col = BoxLayout(orientation="vertical", spacing=dp(2), size_hint=(1, None))
        bar_col.bind(minimum_height=lambda inst, val: setattr(inst, "height", val))  # type: ignore

        self.lbl = Label(
            text="",
            markup=True,
            size_hint=(1, None),
            height=dp(26),
            halign=("left" if self.direction == "ltr" else "right"),
            valign="middle",
            shorten=True,
            shorten_from="right",
        )
        self.lbl.bind(
            size=lambda inst, val: setattr(inst, "text_size", (val[0], None)),  # type: ignore
            texture_size=lambda inst, size: setattr(inst, "height", max(dp(18), size[1])),  # type: ignore
        )

        self.bar = _PredictedLossHealthBar(size_hint=(1, None), height=self.bar_height, direction=self.direction)
        bar_col.add_widget(self.lbl)
        bar_col.add_widget(self.bar)

        if self.direction == "ltr":
            row.add_widget(self.icon)
            row.add_widget(self._spacer)
            row.add_widget(bar_col)
        else:
            row.add_widget(bar_col)
            row.add_widget(self._spacer)
            row.add_widget(self.icon)

        self.stats = GridLayout(cols=2, spacing=dp(4), row_default_height=dp(16), size_hint=(1, None))
        self.stats.bind(minimum_height=lambda inst, val: setattr(inst, "height", val))  # type: ignore
        self.add_widget(self.stats)

    def clear(self) -> None:
        self.name_text = ""
        self.lbl.text = ""
        self.icon.opacity = 0.0
        self.bar.max_value = 0.0
        self.bar.current_value = 0.0
        self.bar.predicted_loss = 0.0
        self.stats.clear_widgets()

    def set_unit(
        self,
        unit: "UnitType | None",
        use_name: bool = True,
        icon_fallback_char: Optional[str] = None,
    ) -> None:
        if unit is None:
            self.clear()
            return

        color = Colors.to_hex(unit.get_owner().civilization.color, strip_alpha=True)
        self.name_text = (
            str(f"{str(unit.name)} - [color={color}]{str(unit.get_owner().civilization.name)}[/color]")
            if use_name
            else ""
        )
        self.lbl.text = f"[b]{self.name_text}[/b]" if self.name_text else ""

        self.bar.max_value = float(getattr(unit, "max_health", 10.0))
        self.bar.current_value = float(getattr(unit, "health_left", self.bar.max_value))
        self.bar.predicted_loss = 0.0

        icon_any = getattr(unit, "icon", None)
        if isinstance(icon_any, str):
            img: Image = AssetManager.load_kivy_image(f"{PathsHelper.get_base_path()}/assets/icons/default/{icon_any}")
            try:
                if hasattr(img, "texture") and img.texture is not None:
                    self.icon.texture = img.texture
                elif hasattr(img, "source"):
                    self.icon.source = img.source  # type: ignore
            except Exception:
                pass
            self.icon.opacity = 1.0
        else:
            self.icon.opacity = 0.0
            if icon_fallback_char:
                self.lbl.text = f"[b]{icon_fallback_char}[/b]  {self.lbl.text}"

        self._rebuild_stats(unit)

    def update_numbers_from_unit(self, unit: "UnitType") -> None:
        self.bar.max_value = float(getattr(unit, "max_health", self.bar.max_value))
        self.bar.current_value = float(getattr(unit, "health_left", self.bar.current_value))

        self._rebuild_stats(unit)

    def set_predicted_loss(self, dmg: float) -> None:
        self.bar.predicted_loss = float(max(0.0, dmg))

    def set_glow_alpha(self, a: float) -> None:
        self.bar.set_glow_alpha(a)

    @staticmethod
    def _fmt_num(v: Any) -> str:
        try:
            f = float(v)
            return str(int(f)) if abs(f - round(f)) < 1e-6 else f"{f:.2f}"
        except Exception:
            return str(v)

    def _add_stat_row(self, key: str, value: str) -> None:
        k = Label(text=f"[b]{key}[/b]", markup=True, size_hint=(1, None), halign="left", valign="middle")
        v = Label(text=value, markup=True, size_hint=(1, None), halign="right", valign="middle")
        for lab in (k, v):
            lab.height = dp(16)
            lab.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))  # type: ignore
            lab.bind(texture_size=lambda inst, size: setattr(inst, "height", max(dp(16), size[1])))  # type: ignore
        self.stats.add_widget(k)
        self.stats.add_widget(v)

    def _rebuild_stats(self, unit: "UnitType") -> None:
        self.stats.clear_widgets()

        # HP
        hp_cur = getattr(unit, "health_left", None)
        hp_max = getattr(unit, "max_health", None)
        self._add_stat_row("HP", f"{self._fmt_num(hp_cur)}/{self._fmt_num(hp_max)}")

        # Melee
        melee_atk = getattr(unit, "attack_power_mele", None)
        melee_def = getattr(unit, "defense_mele", None)
        self._add_stat_row(
            "Melee",
            f"ATK {self._fmt_num(melee_atk or 0)} / DEF {self._fmt_num(melee_def or 0)}",
        )

        # Ranged
        rng_atk = getattr(unit, "attack_power_ranged", None)
        rng_def = getattr(unit, "defense_ranged", None)
        self._add_stat_row(
            "Ranged",
            f"ATK {self._fmt_num(rng_atk or 0)} / DEF {self._fmt_num(rng_def or 0)}",
        )

        # Armor Pen
        apen = getattr(unit, "attack_armor_penetration", None)
        self._add_stat_row("Armor Pen", self._fmt_num(apen))

        # Attack Points
        ap_left = getattr(unit, "attack_points_left", None)
        ap_max = getattr(unit, "attack_points", None)
        self._add_stat_row("AP", f"{self._fmt_num(ap_left)}/{self._fmt_num(ap_max)}")

        # AP Costs (optional)
        apc_m = getattr(unit, "attack_points_cost_mele", None)
        apc_r = getattr(unit, "attack_points_cost_ranged", None)
        self._add_stat_row("AP Cost", f"M {self._fmt_num(apc_m or 0)} / R {self._fmt_num(apc_r or 0)}")

        # Movement
        mv_left = getattr(unit, "moves_left", None)
        mv_max = getattr(unit, "max_moves", None)
        self._add_stat_row("Moves", f"{self._fmt_num(mv_left)}/{self._fmt_num(mv_max)}")


class TargetingDuelPanel(BoxLayout, DirectObject):
    def __init__(self, **kwargs: Any):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("spacing", dp(4))
        kwargs.setdefault("padding", dp(6))
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("width", dp(900))
        kwargs.setdefault("height", dp(250))
        kwargs.setdefault("pos", (dp(775), dp(100)))

        super().__init__(**kwargs)

        self._bg_rect: Optional[Rectangle] = None
        self._pulse_ev = None
        self._pulse_t = 0.0

        with self.canvas.before:
            Color(0, 0, 0, 0.70)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)  # type: ignore

        self.bind(
            pos=lambda inst, val: setattr(self._bg_rect, "pos", val),  # type: ignore
            size=lambda inst, val: setattr(self._bg_rect, "size", val),  # type: ignore
        )

        self.header = Label(
            text=f"[b]{str(t_('ui.player_ui.targeting.targeting'))}[/b]",
            markup=True,
            size_hint=(1, None),
            height=dp(32),
            halign="center",
            valign="middle",
        )
        self.header.bind(size=lambda inst, val: setattr(inst, "text_size", val))  # type: ignore
        self.add_widget(self.header)

        mid = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint=(1, 1))
        self.add_widget(mid)

        self.left = _UnitSide(direction="ltr")
        self._right = _UnitSide(direction="rtl")

        self.vs = Label(
            text=f"[b]{str(t_('ui.player_ui.targeting.versus'))}[/b]",
            markup=True,
            size_hint=(None, 1),
            width=dp(30),
            halign="center",
            valign="middle",
        )
        self.vs.bind(size=lambda inst, val: setattr(inst, "text_size", val))  # type: ignore

        mid.add_widget(self.left)
        mid.add_widget(self.vs)
        mid.add_widget(self._right)

        self._pulse_ev = Clock.schedule_interval(self._tick_pulse, 1 / 30.0)

        self._attacker: Optional["UnitType"] = None
        self._defender: Optional["UnitType"] = None

    def update(self) -> None:
        self.refresh_from_units()

    def _toggle_defender_ui(self, enabled: bool) -> None:
        if enabled:
            self.vs.text = "[b]vs[/b]"
            self.vs.opacity = 1.0
            self.vs.size_hint_x = None
            self.vs.width = dp(30)

            self._right.opacity = 1.0
            self._right.size_hint_x = 1
            self._right.width = 0
        else:
            self.vs.text = ""
            self.vs.opacity = 0.0
            self.vs.size_hint_x = None
            self.vs.width = 0

            self._right.clear()
            self._right.opacity = 0.0
            self._right.size_hint_x = None
            self._right.width = 0

    def set_units(self, attacker: "UnitType", defender: "UnitType | None" = None, simulate_combat: bool = True) -> None:
        self._attacker = attacker
        self._defender = defender

        try:
            title = t_("ui.player_ui.targeting.targeting" if defender else "ui.player_ui.targeting.unit_info")
        except Exception:
            title = "Targeting" if defender else "Unit Info"
        self.header.text = f"[b]{title}[/b]"

        self.left.set_unit(attacker, use_name=True)
        self._right.set_unit(defender, use_name=True)
        self._toggle_defender_ui(defender is not None)

        for side in (self.left, self._right):
            side.lbl.opacity = 1
            side.lbl.size_hint_y = None
            side.lbl.height = dp(18)

        if simulate_combat:
            self.set_prediction(*self.predict_combat())

        try:
            if hasattr(attacker, "get_owner"):
                col = Colors.GREEN
                self.left.bar.fill_color = list(col)
        except Exception:
            pass
        try:
            if defender is not None and hasattr(defender, "get_owner"):
                col = Colors.GREEN
                self._right.bar.fill_color = [col[0] * 0.6 + 0.2, col[1] * 0.6 + 0.2, col[2] * 0.6 + 0.2, 1.0]
        except Exception:
            pass

    def predict_combat(self) -> Tuple[float, float]:
        from sciv.managers.combat import Combat

        if self._attacker is None or self._defender is None:
            return 0.0, 0.0

        outcome = Combat.attack(self._attacker, self._defender, simulation=True)
        return outcome.defender_damage, outcome.attacker_damage

    def refresh_from_units(self) -> None:
        if self._attacker is not None:
            self.left.update_numbers_from_unit(self._attacker)
        if self._defender is not None:
            self._right.update_numbers_from_unit(self._defender)

    def set_prediction(self, attacker_hits: float, defender_hits: float) -> None:
        self.left.set_predicted_loss(attacker_hits)
        self._right.set_predicted_loss(defender_hits)

    def clear_prediction(self) -> None:
        self.left.set_predicted_loss(0.0)
        self._right.set_predicted_loss(0.0)

    def on_parent(self, instance: Widget, parent: Optional[Widget]) -> None:  # type: ignore
        if parent is None and self._pulse_ev is not None:
            self._pulse_ev.cancel()  # type: ignore
            self._pulse_ev = None

    def _tick_pulse(self, dt: float) -> None:
        self._pulse_t += dt * 4.0
        phase = 0.5 + 0.5 * sin(self._pulse_t)  # 0..1
        a = self.left.bar.loss_alpha_base + self.left.bar.loss_alpha_var * phase
        self.left.set_glow_alpha(a)
        self._right.set_glow_alpha(a)

    def destroy(self) -> None:
        if self._pulse_ev is not None:
            self._pulse_ev.cancel()  #   type: ignore
            self._pulse_ev = None
