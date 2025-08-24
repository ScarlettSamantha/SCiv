from typing import TYPE_CHECKING, Any, Optional

from direct.showbase.DirectObject import DirectObject
from helpers.colors import Colors
from helpers.paths import PathsHelper
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from managers.assets import AssetManager
from managers.i18n import t_

if TYPE_CHECKING:
    from gameplay.unit import Unit as UnitType


class UnitSummaryPanel(BoxLayout, DirectObject):
    def __init__(self, **kwargs: Any):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("spacing", dp(6))
        kwargs.setdefault("padding", (dp(8), dp(8), dp(8), dp(8)))
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("width", dp(350))
        kwargs.setdefault("height", dp(350))
        kwargs.setdefault("pos", (dp(425), dp(0)))

        super().__init__(**kwargs)

        self._bg_rect: Optional[Rectangle] = None

        with self.canvas.before:
            Color(0, 0, 0, 0.70)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)  # type: ignore

        self.bind(
            pos=self._on_resize_move,
            size=self._on_resize_move,
        )

        try:
            title = t_("ui.player_ui.unit_info.title")
        except Exception:
            title = "Unit"
        self.header = Label(
            text=f"[b]{title}[/b]",
            markup=True,
            size_hint=(1, None),
            height=dp(26),
            halign="left",
            valign="middle",
        )
        self.header.bind(size=lambda inst, val: setattr(inst, "text_size", val))  # type: ignore
        self.add_widget(self.header)

        top = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint=(1, None), height=dp(64))
        self.add_widget(top)

        self.icon = Image(size_hint=(None, None), size=(dp(56), dp(56)))
        top.add_widget(self.icon)

        name_col = BoxLayout(orientation="vertical", spacing=dp(2))
        top.add_widget(name_col)

        self.name_lbl = Label(
            text="",
            markup=True,
            size_hint=(1, None),
            height=dp(22),
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right",
        )
        self.name_lbl.bind(
            size=lambda inst, val: setattr(inst, "text_size", (val[0], None)),  # type: ignore
            texture_size=lambda inst, size: setattr(inst, "height", max(dp(18), size[1])),  # type: ignore
        )
        name_col.add_widget(self.name_lbl)

        self.civ_lbl = Label(
            text="",
            markup=True,
            size_hint=(1, None),
            height=dp(18),
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right",
        )
        self.civ_lbl.bind(
            size=lambda inst, val: setattr(inst, "text_size", (val[0], None)),  # type: ignore
            texture_size=lambda inst, size: setattr(inst, "height", max(dp(16), size[1])),  # type: ignore
        )
        name_col.add_widget(self.civ_lbl)

        self.stats = GridLayout(
            cols=2,
            spacing=dp(4),
            row_default_height=dp(18),
            size_hint=(1, 1),
        )
        self.stats.bind(minimum_height=lambda inst, val: setattr(inst, "height", val))  # type: ignore
        self.add_widget(self.stats)

        self._unit: Optional["UnitType"] = None

    def set_unit(self, unit: "UnitType | None") -> None:
        self._unit = unit
        if unit is None:
            self._clear()
            return

        unit_name = str(getattr(unit, "name", ""))
        civ_name = ""
        civ_hex = "#CCCCCC"
        try:
            civ = unit.get_owner().civilization
            civ_name = str(getattr(civ, "name", ""))
            civ_hex = Colors.to_hex(civ.color, strip_alpha=True)
        except Exception:
            pass

        self.name_lbl.text = f"[b]{unit_name}[/b]" if unit_name else ""
        self.civ_lbl.text = f"[color={civ_hex}]{civ_name}[/color]" if civ_name else ""

        icon_any = getattr(unit, "icon", None)
        self.icon.opacity = 0.0
        if isinstance(icon_any, string_types := (str,)):  # type: ignore
            try:
                img = AssetManager.load_kivy_image(f"{PathsHelper.get_base_path()}/assets/icons/default/{icon_any}")
                if hasattr(img, "texture") and img.texture is not None:
                    self.icon.texture = img.texture
                elif hasattr(img, "source"):
                    self.icon.source = img.source  # type: ignore
                self.icon.opacity = 1.0
            except Exception:
                pass

        self._rebuild_stats(unit)

    def refresh_from_unit(self) -> None:
        if self._unit is not None:
            self._rebuild_stats(self._unit)

    def _on_resize_move(self, *_: Any) -> None:
        if self._bg_rect is not None:
            self._bg_rect.pos = self.pos  # type: ignore
            self._bg_rect.size = self.size  # type: ignore

    def _clear(self) -> None:
        self.name_lbl.text = ""
        self.civ_lbl.text = ""
        self.icon.opacity = 0.0
        self.stats.clear_widgets()

    @staticmethod
    def _fmt_num(v: Any) -> str:
        try:
            f = float(v)
            return str(int(f)) if abs(f - round(f)) < 1e-6 else f"{f:.2f}"
        except Exception:
            return str(v)

    def _add_stat_row(self, key: str, val: str) -> None:
        k = Label(text=f"[b]{key}[/b]", markup=True, size_hint=(1, None), halign="left", valign="middle")
        v = Label(text=val, markup=True, size_hint=(1, None), halign="right", valign="middle")
        for lab in (k, v):
            lab.height = dp(18)
            lab.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))  # type: ignore
            lab.bind(texture_size=lambda inst, size: setattr(inst, "height", max(dp(16), size[1])))  # type: ignore
        self.stats.add_widget(k)
        self.stats.add_widget(v)

    def _rebuild_stats(self, unit: "UnitType") -> None:
        self.stats.clear_widgets()

        hp_cur = getattr(unit, "health_left", None)
        hp_max = getattr(unit, "max_health", None)
        self._add_stat_row("HP", f"{self._fmt_num(hp_cur)}/{self._fmt_num(hp_max)}")

        mv_left = getattr(unit, "moves_left", None)
        mv_max = getattr(unit, "max_moves", None)
        self._add_stat_row("Moves", f"{self._fmt_num(mv_left)}/{self._fmt_num(mv_max)}")

        ap_left = getattr(unit, "attack_points_left", None)
        ap_max = getattr(unit, "attack_points", None)
        self._add_stat_row("AP", f"{self._fmt_num(ap_left)}/{self._fmt_num(ap_max)}")

        melee_atk = getattr(unit, "attack_power_mele", None)
        melee_def = getattr(unit, "defense_mele", None)
        self._add_stat_row("Melee", f"ATK {self._fmt_num(melee_atk or 0)} / DEF {self._fmt_num(melee_def or 0)}")

        rng_atk = getattr(unit, "attack_power_ranged", None)
        rng_def = getattr(unit, "defense_ranged", None)
        self._add_stat_row("Ranged", f"ATK {self._fmt_num(rng_atk or 0)} / DEF {self._fmt_num(rng_def or 0)}")

        rng = getattr(unit, "attack_range", None)
        if rng is not None:
            self._add_stat_row("Range", self._fmt_num(rng))

        apen = getattr(unit, "attack_armor_penetration", None)
        if apen is not None:
            self._add_stat_row("Armor Pen", self._fmt_num(apen))
