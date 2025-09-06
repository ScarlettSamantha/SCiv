from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional

from direct.showbase.DirectObject import DirectObject
from gameplay.civilization import Civilization
from gameplay.player import Player
from gameplay.resource import BaseResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.tile import Tile
from gameplay.unit import Unit
from gameplay.yields import Yields
from helpers.colors import Colors
from helpers.paths import PathsHelper
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from managers.assets import AssetManager
from managers.entity import EntityType
from managers.i18n import t_

if TYPE_CHECKING:
    from gameplay.tile import Tile as TileType
    from gameplay.unit import Unit as UnitType


class TargetPanel(BoxLayout, DirectObject):
    def __init__(self, **kwargs: Any):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("spacing", dp(6))
        kwargs.setdefault("padding", (dp(8), dp(8), dp(8), dp(8)))
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("width", dp(400))
        kwargs.setdefault("height", dp(500))
        kwargs.setdefault("pos", (dp(0), dp(0)))
        super().__init__(**kwargs)

        self._bg_rect: Optional[Rectangle] = None
        with self.canvas.before:
            Color(0, 0, 0, 0.70)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)  # type: ignore

        self.bind(pos=self._on_resize_move, size=self._on_resize_move)

        try:
            self._title_unit = t_("ui.player_ui.unit_info.title")
        except Exception:
            self._title_unit = "Unit"

        try:
            self._title_tile = t_("ui.player_ui.tile_info.title")
        except Exception:
            self._title_tile = "Tile"

        self.header = Label(
            text=f"[b]{self._title_unit}[/b]",
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
        self._tile: Optional["TileType"] = None
        self._mode: str = "unit"

    def show_for(self, obj: "Unit | Tile") -> None:
        if obj.entity_type_ref == EntityType.TILE.value[0]:  #   type: ignore
            self.set_tile(obj)  # type: ignore
        elif obj.entity_type_ref == EntityType.UNIT.value[0]:  # type: ignore
            self.set_unit(obj)  # type: ignore
        else:
            raise ValueError(f"Unsupported type for show_for(): {type(obj)}")

    def set_unit(self, unit: "UnitType | None") -> None:
        self._mode = "unit"
        self.header.text = f"[b]{self._title_unit}[/b]"
        self._tile = None
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

        self._set_icon_from_attr(getattr(unit, "icon", None))
        self._rebuild_stats_unit(unit)

    def refresh_from_unit(self) -> None:
        if self._mode == "unit" and self._unit is not None:
            self._rebuild_stats_unit(self._unit)

    def set_tile(self, tile: "TileType | None") -> None:
        self._mode = "tile"
        self.header.text = f"[b]{self._title_tile}[/b]"
        self._unit = None
        self._tile = tile
        if tile is None:
            self._clear()
            return

        terrain: BaseTerrain = tile.get_terrain()
        terrain_name = str(terrain.get_name())

        tile_coords = f"{getattr(tile, 'x', '?')},{getattr(tile, 'y', '?')}"
        self.name_lbl.text = f"[b]{terrain_name}[/b]" if terrain_name else f"[b]Tile {tile_coords}[/b]"

        owner: Player = tile.get_owner()
        owner_name = owner.get_name_short() if owner else "Nature"
        civ: Civilization = owner.get_civilization()
        owner_hex = Colors.to_hex(civ.color, strip_alpha=True)
        self.civ_lbl.text = f"[color={owner_hex}]{owner_name or 'Nature'}[/color]"

        self._rebuild_stats_tile(tile)

    def refresh_from_tile(self) -> None:
        if self._mode == "tile" and self._tile is not None:
            self._rebuild_stats_tile(self._tile)

    def _on_resize_move(self, *_: Any) -> None:
        if self._bg_rect is not None:
            self._bg_rect.pos = self.pos  # type: ignore
            self._bg_rect.size = self.size  # type: ignore

    def _clear(self) -> None:
        self.name_lbl.text = ""
        self.civ_lbl.text = ""
        self.icon.opacity = 0.0
        self.icon.texture = None  # type: ignore
        self.icon.source = ""  # type: ignore
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

    def _set_icon_from_attr(self, icon_any: Any) -> None:
        self.icon.opacity = 0.0
        if isinstance(icon_any, str) and icon_any:
            try:
                img = AssetManager.load_kivy_image(f"{PathsHelper.get_base_path()}/assets/icons/default/{icon_any}")
                if hasattr(img, "texture") and img.texture is not None:
                    self.icon.texture = img.texture
                elif hasattr(img, "source"):
                    self.icon.source = img.source  # type: ignore
                self.icon.opacity = 1.0
            except Exception:
                pass

    def _rebuild_stats_unit(self, unit: "UnitType") -> None:
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

    def _rebuild_stats_tile(self, tile: "TileType") -> None:
        self.stats.clear_widgets()

        x = tile.x
        y = tile.y
        self._add_stat_row("Coords", f"{x},{y}")

        altitude = tile.altitude
        self._add_stat_row(str(t_("world.stats.altitude")), self._fmt_num(altitude))
        self._add_stat_row(str(t_("world.stats.temperature")), self._fmt_num(tile.temperature))
        self._add_stat_row(str(t_("world.stats.moisture")), self._fmt_num(tile.moisture))

        terrain: BaseTerrain = tile.get_terrain()

        name = getattr(terrain, "name", None)
        if name:
            self._add_stat_row("Terrain", str(tile.get_terrain().name))

        owner: Player | Any | None = tile.get_owner()
        self._add_stat_row("Owner", str(getattr(owner, "name", None)))

        passable = getattr(tile, "passable", None)
        walkable = getattr(tile, "walkable", None)
        climbable = getattr(tile, "climbable", None)
        if passable is not None:
            self._add_stat_row("Passable", "Yes" if passable else "No")
        if walkable is not None:
            self._add_stat_row("Walkable", "Yes" if walkable else "No")
        if climbable is not None:
            self._add_stat_row("Climbable", "Yes" if climbable else "No")

        mv_cost = None
        try:
            mv_cost = tile.movement_cost
        except Exception:
            pass
        if mv_cost is not None:
            self._add_stat_row("Move Cost", self._fmt_num(mv_cost))

        yld: Yields = tile.get_tile_yield()

        self._add_stat_row(str(t_("content.resources.food.name")), self._fmt_num(yld.food.value))
        self._add_stat_row(str(t_("content.resources.production.name")), self._fmt_num(yld.production.value))
        self._add_stat_row(str(t_("content.resources.gold.name")), self._fmt_num(yld.gold.value))
        self._add_stat_row(str(t_("content.resources.science.name")), self._fmt_num(yld.science.value))
        self._add_stat_row(str(t_("content.resources.culture.name")), self._fmt_num(yld.culture.value))
        self._add_stat_row(str(t_("content.resources.faith.name")), self._fmt_num(yld.faith.value))

        resources_line = self._summarize_names(self._iter_resource_names(tile))
        if resources_line:
            self._add_stat_row("Resources", resources_line)

        improvements_line = self._summarize_names(self._iter_improvement_names(tile))
        if improvements_line:
            self._add_stat_row("Improvements", improvements_line)

    def _summarize_names(self, items: Iterable[str], max_items: int = 4) -> str:
        arr: List[str] = [str(s) for s in items if s]
        if not arr:
            return ""
        if len(arr) <= max_items:
            return ", ".join(arr)
        return ", ".join(arr[:max_items]) + f" (+{len(arr) - max_items})"

    def _iter_resource_names(self, tile: Tile) -> Iterable[str]:
        try:
            res: Dict[str, BaseResource] = tile.get_resources().flatten_non_mechanic()
            if not res:
                return []
            return [str(r.name) for r in res.values()]
        except Exception:
            return []

    def _iter_improvement_names(self, tile: Any) -> Iterable[str]:
        try:
            imp_set = tile.get_improvements()
            if not imp_set:
                return []
            return [str(imp.name) for imp in imp_set]
        except Exception:
            pass
        return []
