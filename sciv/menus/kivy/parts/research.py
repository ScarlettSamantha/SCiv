from collections import defaultdict
from typing import TYPE_CHECKING, Any, Dict, List, Tuple, Type

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from gameplay.tech import Tech, TechTree
from helpers.colors import Colors
from helpers.optimizations import throttle
from helpers.os import WindowsHelper
from helpers.placeholder import Placeholder
from kivy.animation import Animation
from kivy.graphics import Color, Line, Rectangle  # type: ignore
from kivy.metrics import dp  # type: ignore
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from managers.i18n import T_TranslationOrStr, Translation
from managers.player import PlayerManager
from menus.kivy.elements.horizontal_scroll import HorizontalScrollView
from menus.kivy.elements.tooltip import TooltippedButton, TooltippedImage
from system.entity import BaseEntity

if TYPE_CHECKING:
    from menus.screens.game_ui import GameUIScreen  # type: ignore


class _ColorChip(Widget):
    def __init__(self, rgba: Tuple[float, float, float, float], **kwargs: Any):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(12), dp(12))
        with self.canvas:  #     type: ignore
            self._c = Color(*rgba)
            self._r = Rectangle(pos=self.pos, size=self.size)  # type: ignore
        self.bind(pos=self._sync, size=self._sync)  # type: ignore

    def _sync(self, *a: Any):
        self._r.pos = self.pos
        self._r.size = self.size  # type: ignore


class LegendFrame(BoxLayout):
    def __init__(self, items: Dict[Tuple[float, float, float, float], str], **kwargs: Dict[str, Any]):
        super().__init__(**kwargs)  # type: ignore
        self.orientation = "vertical"
        self.spacing = dp(6)
        self.padding = (dp(10), dp(8), dp(10), dp(8))
        self.size_hint = (None, None)
        with self.canvas.before:
            self._bg_c = Color(0, 0, 0, 0.6)
            self._bg = Rectangle(pos=self.pos, size=self.size)  # type: ignore
        self.bind(pos=self._sync, size=self._sync)  # type: ignore
        for rgba, text in items.items():
            row = BoxLayout(orientation="horizontal", size_hint=(None, None), height=dp(18), spacing=dp(8))
            chip = _ColorChip(rgba)
            lbl = Label(text=text, size_hint=(None, None), height=dp(18), valign="middle", halign="left")
            lbl.bind(texture_size=lambda _l, s: setattr(_l, "width", s[0]))  # type: ignore
            row.add_widget(chip)
            row.add_widget(lbl)
            row.bind(minimum_width=lambda r, w: setattr(r, "width", w))  # type: ignore
            self.add_widget(row)
        self.bind(minimum_height=lambda _w, h: setattr(self, "height", h))  # type: ignore
        self.bind(minimum_width=lambda _w, w: setattr(self, "width", w))  # type: ignore

    def _sync(self, *a: Any):
        self._bg.pos = self.pos
        self._bg.size = self.size  # type: ignore


class ResearchButton(TooltippedButton):
    fade_alpha = NumericProperty(0.0)

    def __init__(
        self,
        value: Type[Tech],
        unlocks: List[Type[Tech] | Type["BaseEntity"]] = [],
        size: Tuple[int, int] = (250, 72),
        cost: int = 0,
        *args: Any,
        **kwargs: Any,
    ):
        self.value: Type[Tech] = value
        self.is_researching = PlayerManager.session_player().tech.is_researching(self.value)
        self.cost = value.tech_points_required

        if self.is_researching:
            self._cost_text: str = f"{str(PlayerManager.session_player().tech.current_science)}/{str(self.cost)}"
        else:
            self._cost_text: str = f"{str(self.cost)}"

        self._unlocks: List[Type[Tech] | Type["BaseEntity"]] = unlocks

        super().__init__(*args, **kwargs)
        self.width = dp(size[0])
        self.height = dp(size[1])

        with self.canvas.after:
            self._fade_color = Color(0, 0, 0, self.fade_alpha)
            self._fade_rect = Rectangle(pos=self.pos, size=self.size)  # type: ignore

        self.bind(pos=self._update_fade_rect, size=self._update_fade_rect)  # type: ignore
        self.bind(fade_alpha=self._update_fade_opacity)  # type: ignore

        self._is_hovered = False
        self.clear_widgets()

        self._title_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(24),
            spacing=dp(4),  # type: ignore
            padding=(dp(2), 0, 0, 0),
        )

        tech_icon_src = getattr(value, "icon", Placeholder.getPlaceholderImagePathSmallIcon())

        if WindowsHelper.is_windows():
            tech_icon_src = WindowsHelper.unix_to_win32_path(tech_icon_src)

        requires = [str(entry.name) for entry in self.value.requires]
        tooltip_text = value.on_tooltip() if hasattr(value, "on_tooltip") else getattr(value, "name", "Unknown Tech")
        tooltip_text += f"\n\nRequires:\n- {'\n- '.join(requires) if requires else 'None'}"

        self.tech_icon = TooltippedImage(
            source=tech_icon_src,
            tooltip_text=tooltip_text,
            tooltip_image_source=tech_icon_src,
            tooltip_markup=True,
            tooltip_multiline=True,
            size_hint=(None, None),
            size=(dp(20), dp(20)),
            allow_stretch=True,
            keep_ratio=True,
            spacing=dp(2),
            border_color=getattr(value, "icon_border_color", (1, 1, 1, 1)),
        )

        self._name_lbl = Label(
            text=self.primary_text,
            size_hint_x=0.65,
            halign="left",
            valign="middle",
            text_size=(None, None),  # type: ignore
        )
        self._cost_lbl = Label(
            text=self._cost_text,
            size_hint_x=0.3,
            halign="right",
            valign="middle",
            text_size=(None, None),  # type: ignore
        )

        self._title_row.add_widget(self.tech_icon)
        self._title_row.add_widget(self._name_lbl)
        self._title_row.add_widget(self._cost_lbl)

        self._second_line = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(32),
            spacing=dp(3),  # type: ignore
            padding=(dp(2), 0, dp(2), dp(2)),
        )
        self._refresh_second_line()

        self.add_widget(self._title_row)
        spacer = Widget(size_hint_y=None, height=dp(4))  # type: ignore
        self.add_widget(spacer)
        self.add_widget(self._second_line)

        self._title_row.bind(minimum_height=self._title_row.setter("height"))  # type: ignore
        self._second_line.bind(minimum_height=self._second_line.setter("height"))  # type: ignore

    def _update_fade_opacity(self, *args: Any):
        self._fade_color.a = self.fade_alpha

    def _update_fade_rect(self, *args: Any):
        self._fade_rect.pos = self.pos
        self._fade_rect.size = self.size

    def _on_primary_text(self, _, new: str):
        if hasattr(self, "_name_lbl"):
            self._name_lbl.text = new

    def _refresh_second_line(self, *args: Any):
        self._second_line.clear_widgets()

        icon_size = dp(24)
        placeholder = Placeholder.getPlaceholderImagePathSmallIcon

        for tech_type in self._unlocks:
            src = getattr(tech_type, "icon", placeholder())
            tip = getattr(tech_type, "name", "Unknown Tech Type")

            border_color = getattr(tech_type, "icon_border_color", (1, 1, 1, 1))

            if isinstance(src, (T_TranslationOrStr)):
                src = str(str(src))
            if isinstance(tip, (T_TranslationOrStr)):
                tip = str(tip)

            if WindowsHelper.is_windows():
                src = WindowsHelper.unix_to_win32_path(src)

            tooltip_text = tech_type.on_tooltip() if hasattr(tech_type, "on_tooltip") else tip  # type: ignore

            img = TooltippedImage(
                source=src,
                tooltip_text=tooltip_text,
                tooltip_markup=False,
                tooltip_multiline=True,
                tooltip_image_source=src,
                size_hint=(None, None),
                size=(icon_size, icon_size),
                allow_stretch=True,
                keep_ratio=True,
                border_color=border_color,
                padding=2,
                border_size=1,
            )
            self._second_line.add_widget(img)

        if not self.secondary_text:
            self.secondary_text = ""

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

    def _refresh_content(self):
        self.is_researching = PlayerManager.session_player().tech.is_researching(self.value)
        if self.is_researching:
            self.cost_remaining = PlayerManager.session_player().tech.current_science
            self._cost_text = f"{self.cost_remaining}/{self.cost}"
        else:
            self._cost_text = f"{self._cost_text.split('/')[-1]}"

        if hasattr(self, "_cost_lbl"):
            self._cost_lbl.text = self._cost_text

        if hasattr(self, "_name_lbl"):
            self._name_lbl.text = self.primary_text

        self._refresh_second_line()

    def on_release(self):
        if self.disabled:
            return
        super().on_release()  #  type: ignore
        self._refresh_content()

    def destroy(self) -> None:
        [widget.destroy() for widget in self._title_row.children if hasattr(widget, "destroy")]  # type: ignore
        [widget.destroy() for widget in self._second_line.children if hasattr(widget, "destroy")]  # type: ignore
        self.unbind(on_release=self.on_release)
        self.clear_widgets()
        self.canvas.after.clear()
        self.canvas.before.clear()
        self.canvas.clear()
        super().destroy()


class Research(FloatLayout, DirectObject):
    def __init__(self, tree: TechTree, manager: "GameUIScreen", **kwargs: Any) -> None:
        FloatLayout.__init__(self, **kwargs)  # type: ignore
        DirectObject.__init__(self, **kwargs)
        self.manager = manager
        self.tree = tree
        self.player = PlayerManager.session_player()
        self.player_tech_manager = self.player.tech
        self._column_width = 450
        self._button_width = 180
        self._button_height = 60
        self._padding_left = 50
        self._vertical_spacing = 40
        self._box_margin = 10
        self._is_build = False
        self._level_colors = {}
        self._hovered_tech = None
        self.is_open = True
        self.popup_disabled = True
        self._buttons = {}
        self._line_refs: List[Any] = []
        self._arrow_head_refs: List[Any] = []
        self._arrow_box_gap = dp(6)
        self._adjacent_mid_margin = dp(8)
        self._arrow_length = dp(12)
        self._arrow_perp = dp(4)
        self._legend = None
        self.register()

    def destroy(self) -> None:
        self.clear()
        self.is_open = False

    def register(self) -> None:
        self.accept("ui.update.ui.refresh_research_ui", self.update)
        self.bind(height=lambda *_: self.rebuild_layout())

    def update(self, *args: Any) -> None:
        if self.is_open:
            self._calculate_button_state()

    def clear(self) -> None:
        for child in list(self._float_layout.children):
            if isinstance(child, ResearchButton):
                child.unbind(on_release=self.on_research_button_click)

        for ref in self._line_refs:
            self._float_layout.canvas.before.remove(ref["line"])  # type: ignore
            self._float_layout.canvas.before.remove(ref["color"])  # type: ignore
        self._line_refs.clear()

        for arrow in self._arrow_head_refs:
            self._float_layout.canvas.before.remove(arrow["line1"])  # type: ignore
            self._float_layout.canvas.before.remove(arrow["line2"])  # type: ignore
            self._float_layout.canvas.before.remove(arrow["color"])  # type: ignore
        self._arrow_head_refs.clear()

        self._float_layout.clear_widgets()
        [button.destroy() for button in self._buttons.values()]

    def build(self) -> None:
        if self._is_build:
            return

        self.scroll_view = HorizontalScrollView(
            do_scroll_x=True,
            do_scroll_y=False,
            scroll_type=["bars", "content"],
            bar_width=15,
            size_hint=(1, 1),
        )
        # type: ignore

        self._tech_classes: List[Type[Tech]] = list(self.tree.items())  # type: ignore

        self._float_layout = FloatLayout(size_hint=(None, 1), pos_hint={"top": 0, "y": 0})
        self._level_map: Dict[Type[Tech], int] = self._calculate_levels(self._tech_classes)
        max_level = max(self._level_map.values()) if self._level_map else 0
        self._float_layout.width = (max_level + 1) * self._column_width + self._padding_left * 2
        self._float_layout.height = self.height or 1080  # type: ignore

        with self._float_layout.canvas.before:  # type: ignore
            Color(0.1, 0.1, 0.1, 1)  # dark gray background
            self._bg_rect = Rectangle(pos=self._float_layout.pos, size=self._float_layout.size)  # type: ignore
        self._float_layout.bind(pos=self._update_rect, size=self._update_rect)
        self.scroll_view.add_widget(self._float_layout)  # type: ignore

        self._column_bounds: Dict[int, Tuple[float, float]] = {}

        self._tech_by_level: Dict[int, List[Type[Tech]]] = {}

        self.add_widget(self.scroll_view)  # type: ignore
        self._is_build = True
        self.popup_disabled = False

    def _update_rect(self, instance: FloatLayout, value: Any) -> None:
        self._bg_rect.pos = instance.pos  # type: ignore
        self._bg_rect.size = instance.size

    def _calculate_button_state(self) -> None:
        for btn in list(self._buttons.values()):  # type: ignore
            btn: ResearchButton = btn

            btn.disabled = self.player_tech_manager.is_tech_researched(
                btn.value
            ) or not self.player_tech_manager.are_tech_requirements_met(btn.value)

            if self.player_tech_manager.is_tech_researched(btn.value):
                btn.background_color = Colors.YELLOW[:3] + (0.8,)
            elif type(self.player_tech_manager.researching) == btn.value:
                btn.background_color = Colors.BLUE[:3] + (0.8,)
            elif self.player_tech_manager.are_tech_requirements_met(btn.value):
                btn.background_color = Colors.GREEN[:3] + (0.8,)
            else:
                btn.background_color = Colors.GREY[:3] + (0.8,)

    def _calculate_levels(self, techs: List[Type[Tech]]) -> Dict[Type[Tech], int]:
        level_map: Dict[Type[Tech], int] = {}
        changed = True
        while changed:
            changed = False
            for tech_cls in techs:
                reqs = tech_cls.requires
                if not reqs:
                    new_level = 0
                else:
                    new_level = 1 + max(level_map.get(req, 0) for req in reqs)
                if new_level != level_map.get(tech_cls, -1):
                    level_map[tech_cls] = new_level
                    changed = True
        return level_map

    def _place_tech_buttons(self) -> None:
        self._tech_by_level = {}
        self._level_map = self._calculate_levels(self._tech_classes)
        self._column_bounds = {}
        self._buttons: Dict[Any, Any] = {}

        tech_by_level: Dict[int, List[Type[Tech]]] = defaultdict(list)
        for tech_cls in self._tech_classes:
            lvl: int = self._level_map[tech_cls]
            tech_by_level[lvl].append(tech_cls)

        sorted_tech_by_level: Dict[int, List[Type[Tech]]] = {}
        for level in sorted(tech_by_level.keys()):
            if level == 0:
                sorted_tech_by_level[level] = sorted(tech_by_level[level], key=lambda tech: tech.key)
            else:
                prev_sorted = sorted_tech_by_level.get(level - 1, [])
                prev_index = {tech: i for i, tech in enumerate(prev_sorted)}

                def sort_key(tech: Type[Tech]) -> Tuple[float, str]:
                    reqs_in_prev = [
                        req for req in tech.requires if self._level_map.get(req) == level - 1 and req in prev_index
                    ]
                    if reqs_in_prev:
                        avg = sum(prev_index[req] for req in reqs_in_prev) / len(reqs_in_prev)
                        return (avg, str(tech.key))
                    return (float("inf"), tech.key)

                sorted_tech_by_level[level] = sorted(tech_by_level[level], key=sort_key)

        self._tech_by_level = sorted_tech_by_level

        layout_height = self.height or 1080  # type: ignore
        total_height = layout_height  # type: ignore

        for level, tech_list in sorted_tech_by_level.items():
            n = len(tech_list)
            spacing = (total_height - n * self._button_height) / (n + 1) if n > 0 else 0  # type: ignore

            col_min_y = float("inf")
            col_max_y = float("-inf")

            for i, tech_cls in enumerate(tech_list):
                x_pos = self._padding_left + level * self._column_width + (self._column_width - self._button_width) / 2
                y_pos = total_height - ((i + 1) * spacing + i * self._button_height + self._button_height)  # type: ignore

                btn = ResearchButton(
                    primary_text=tech_cls.name,
                    secondary_text="",
                    cost=tech_cls.tech_points_required,
                    unlocks=tech_cls.unlocks(),
                    tooltip_text=tech_cls.description,
                    size_hint=(None, None),
                    size=(250, 72),
                    pos=(x_pos, y_pos),
                    value=tech_cls,
                )
                btn.disabled = self.player_tech_manager.is_tech_researched(
                    tech_cls
                ) or not self.player_tech_manager.are_tech_requirements_met(tech_cls)

                btn.bind(on_release=self.on_research_button_click)  # type: ignore

                self._float_layout.add_widget(btn)  # type: ignore
                self._buttons[tech_cls] = btn  # type: ignore

                top_y = y_pos + self._button_height  # type: ignore
                col_min_y = min(col_min_y, y_pos)  # type: ignore
                col_max_y = max(col_max_y, top_y)  # type: ignore

            self._column_bounds[level] = (col_min_y, col_max_y)

        max_level = max(self._level_map.values()) if self._level_map else 0
        self._float_layout.width = (max_level + 1) * self._column_width + self._padding_left * 2
        self._float_layout.height = total_height
        self._calculate_button_state()

    @throttle(0.1)
    def rebuild_layout(self):
        self.clear()
        self._place_tech_buttons()
        self._draw_dependency_lines()
        self._ensure_legend()

    def _ensure_legend(self):
        if not hasattr(self, "_legend") or self._legend is None:
            items: Dict[Tuple[float, float, float, float], str] = {
                Colors.BLUE: str(Translation("ui.player_ui.technology_tree.legenda.blue")),
                Colors.YELLOW: str(Translation("ui.player_ui.technology_tree.legenda.yellow")),
                Colors.RED: str(Translation("ui.player_ui.technology_tree.legenda.red")),
                Colors.GREEN: str(Translation("ui.player_ui.technology_tree.legenda.green")),
            }
            self._legend = LegendFrame(items)
            self._legend.pos = (dp(12), dp(12))
            self._float_layout.add_widget(self._legend)  # type: ignore
        else:
            self._legend.pos = (dp(12), dp(12))
            self._float_layout.add_widget(self._legend)  # type: ignore

    def _highlight_tech(self, tech_cls: Type[Tech]) -> None:
        if self._hovered_tech == tech_cls:
            return

        self._hovered_tech = tech_cls
        related = set(tech_cls.requires + tech_cls.unlocks())
        related.add(tech_cls)

        for t, btn in self._buttons.items():
            fade_to = 0.85 if t not in related else 0.0
            Animation(fade_alpha=fade_to, duration=0.2).start(btn)  # type: ignore

        for ref in getattr(self, "_line_refs", []):
            a, b = ref["tech_pair"]
            color = ref["color"]
            r, g, b_, _ = color.rgba
            target_a = 1.0 if a in related and b in related else 0.15
            Animation(rgba=(r, g, b_, target_a), duration=0.2).start(color)  # type: ignore

    def _clear_highlight(self, *args: Any):
        if self._hovered_tech is None:
            return  # Already cleared

        self._hovered_tech = None

        for btn in self._buttons.values():
            Animation(fade_alpha=0.0, duration=0.2).start(btn)  # type: ignore

        for ref in getattr(self, "_line_refs", []):
            color = ref["color"]
            r, g, b_, _ = color.rgba
            Animation(rgba=(r, g, b_, 1.0), duration=0.2).start(color)  # type: ignore

    def on_research_button_click(self, btn: ResearchButton) -> None:
        if self.disabled is True:
            return
        self.player.on_request_start_research_session(btn.value)
        MessengerGlobal.messenger.send("game.gameplay.research.request_start_research_session_player", [btn.value])
        MessengerGlobal.messenger.send("ui.update.ui.refresh_research_ui")

    def _draw_dependency_lines(self, *args: Any) -> None:
        if not self._buttons or not self._float_layout.canvas:
            return
        self._line_refs = []
        Colors._sequence_index = 0  # type: ignore
        outgoing_counts: Dict[Type[Tech], int] = defaultdict(int)
        incoming_counts: Dict[Type[Tech], int] = defaultdict(int)
        column_lane_counts: Dict[int, int] = defaultdict(int)
        for tech_cls in self._tech_classes:
            for req_cls in tech_cls.requires:
                incoming_counts[tech_cls] += 1
        with self._float_layout.canvas.before:
            for tech_cls in self._tech_classes:
                if tech_cls not in self._buttons:
                    continue
                to_btn = self._buttons[tech_cls]
                tgt_level = self._level_map[tech_cls]
                for req_cls in tech_cls.requires:
                    from_btn = self._buttons.get(req_cls)
                    if not from_btn:
                        continue
                    out_index = outgoing_counts[req_cls]
                    total_out = len([t for t in self._tech_classes if req_cls in t.requires])
                    outgoing_counts[req_cls] += 1
                    out_spacing = dp(10)
                    sy = from_btn.center_y + out_spacing * (out_index - total_out / 2)
                    sx = from_btn.right
                    src_level = self._level_map[req_cls]
                    in_index = incoming_counts[tech_cls] - 1
                    in_total = incoming_counts[tech_cls]
                    in_spacing = dp(33)
                    arrival_y = to_btn.center_y + in_spacing * (in_index - in_total / 2)
                    incoming_counts[tech_cls] -= 1
                    travel_lanes: Dict[int, float] = {}
                    for col in range(min(src_level, tgt_level), max(src_level, tgt_level) + 1):
                        lane_idx = column_lane_counts[col]
                        lane_offset = dp(16) * (lane_idx - 1)
                        travel_lanes[col] = lane_offset
                        column_lane_counts[col] += 1
                    color_val = Colors.sequence()
                    color_instr = Color(*color_val)
                    points = self._build_stepwise_path(src_level, tgt_level, sx, sy, to_btn, arrival_y, travel_lanes)
                    points = self._simplify_polyline(points)
                    line = Line(points=points, width=1.5)
                    self._line_refs.append(
                        {
                            "line": line,
                            "color": color_instr,
                            "tech_pair": (req_cls, tech_cls),
                        }
                    )
                    self._draw_arrowhead(points, color_val)

    def _simplify_polyline(self, pts: List[float]) -> List[float]:
        if len(pts) < 4:
            return pts
        eps = 0.75
        pairs: List[Tuple[float, float]] = []
        last: Tuple[float, float] | None = None
        for i in range(0, len(pts), 2):
            p = (pts[i], pts[i + 1])
            if last is None or abs(p[0] - last[0]) >= eps or abs(p[1] - last[1]) >= eps:
                pairs.append(p)
                last = p
        if len(pairs) <= 2:
            return [c for p in pairs for c in p]
        out: List[Tuple[float, float]] = [pairs[0]]
        for i in range(1, len(pairs) - 1):
            a = out[-1]
            b = pairs[i]
            c = pairs[i + 1]
            dx1 = b[0] - a[0]
            dy1 = b[1] - a[1]
            dx2 = c[0] - b[0]
            dy2 = c[1] - b[1]
            l1 = (dx1 * dx1 + dy1 * dy1) ** 0.5
            l2 = (dx2 * dx2 + dy2 * dy2) ** 0.5
            if l1 < eps or l2 < eps:
                continue
            cross = abs(dx1 * dy2 - dy1 * dx2)
            if cross <= 0.01 * l1 * l2:
                continue
            out.append(b)
        out.append(pairs[-1])
        return [c for p in out for c in p]

    def _get_route_y_for_column(self, col: int, current_y: float, target_y: float, offset: float = 0.0) -> float:
        if col not in self._tech_by_level:
            return current_y + offset

        spans: List[Any] = []
        for tech_cls in self._tech_by_level[col]:
            btn = self._buttons.get(tech_cls)
            if btn:
                spans.append((btn.y, btn.top))  # type: ignore

        spans.sort()  # type: ignore
        margin = dp(6)

        for y0, y1 in spans:  # type: ignore
            if y0 - margin <= current_y <= y1 + margin:
                break
        else:
            return current_y + offset

        step = dp(8)
        max_y = self._float_layout.height  # type: ignore

        for i in range(1, 100):
            for direction in [+1, -1]:
                candidate = current_y + i * step * direction + offset
                if 0 < candidate < max_y:
                    blocked = False
                    for y0, y1 in spans:  # type: ignore
                        if y0 - margin <= candidate <= y1 + margin:
                            blocked = True
                            break
                    if not blocked:
                        return candidate
        return current_y + offset

    def _build_stepwise_path(
        self,
        src_level: int,
        tgt_level: int,
        sx: float,
        sy: float,
        to_btn: ResearchButton,
        arrival_y: float,
        travel_lanes: Dict[int, float],
    ) -> List[float]:
        points: List[float] = [sx, sy]
        current_x, current_y = sx, sy
        going_right = tgt_level > src_level
        step = 1 if going_right else -1
        min_first_dx = dp(18)
        head_clearance = dp(10)
        contact_x = to_btn.x if going_right else to_btn.right
        if abs(tgt_level - src_level) == 1:
            lane_offset = travel_lanes.get(tgt_level, 0.0)
            if going_right:
                safe_end_x = contact_x - (self._arrow_length + head_clearance)
                mid_x = sx + max(dp(40) + lane_offset, min_first_dx)
                mid_x = min(mid_x, safe_end_x - self._adjacent_mid_margin)
                target_x = contact_x
            else:
                safe_end_x = contact_x + (self._arrow_length + head_clearance)
                mid_x = sx - max(dp(40) + lane_offset, min_first_dx)
                mid_x = max(mid_x, safe_end_x + self._adjacent_mid_margin)
                target_x = contact_x
            points.extend([mid_x, current_y])
            points.extend([mid_x, arrival_y])
            points.extend([safe_end_x, arrival_y])
            points.extend([target_x, arrival_y])
            return points
        col = src_level
        first_hop_done = False
        while col != tgt_level:
            next_col = col + step
            boundary_x = (
                self._padding_left + next_col * self._column_width - self._adjacent_mid_margin
                if going_right
                else self._padding_left + next_col * self._column_width + self._button_width + self._adjacent_mid_margin
            )
            boundary_x += travel_lanes.get(next_col, 0.0)
            if not first_hop_done:
                desired = (sx + min_first_dx) if going_right else (sx - min_first_dx)
                if (going_right and boundary_x - sx < min_first_dx) or (
                    not going_right and sx - boundary_x < min_first_dx
                ):
                    if abs(desired - current_x) > 1e-6:
                        points.extend([desired, current_y])
                        current_x = desired
                first_hop_done = True
            if abs(boundary_x - current_x) > 1e-6:
                points.extend([boundary_x, current_y])
                current_x = boundary_x
            route_y = self._get_route_y_for_column(next_col, current_y, arrival_y)
            if abs(route_y - current_y) > 1e-6:
                points.extend([current_x, route_y])
                current_y = route_y
            col = next_col
        final_x = contact_x
        if abs(arrival_y - current_y) > 1e-6:
            points.extend([current_x, arrival_y])
        need_len = self._arrow_length + head_clearance
        if (going_right and final_x - current_x < need_len) or (not going_right and current_x - final_x < need_len):
            safe_end_x = final_x - (need_len if going_right else -need_len)
            if abs(safe_end_x - current_x) > 1e-6:
                points.extend([safe_end_x, arrival_y])
                current_x = safe_end_x
        if abs(final_x - current_x) > 1e-6:
            points.extend([final_x, arrival_y])
        return points

    def _draw_arrowhead(self, points: List[float], color: Tuple[float, float, float, float]) -> None:
        if len(points) < 4:
            return
        x_prev, y_prev = points[-4], points[-3]
        x_tip, y_tip = points[-2], points[-1]
        dx, dy = x_tip - x_prev, y_tip - y_prev
        d = (dx * dx + dy * dy) ** 0.5
        if d < 1e-6:
            return
        ndx, ndy = dx / d, dy / d
        shaft_end_x = x_tip - ndx * self._arrow_length
        shaft_end_y = y_tip - ndy * self._arrow_length
        points[-2], points[-1] = shaft_end_x, shaft_end_y
        px, py = -ndy, ndx
        leftx = x_tip - ndx * self._arrow_length + px * self._arrow_perp
        lefty = y_tip - ndy * self._arrow_length + py * self._arrow_perp
        rightx = x_tip - ndx * self._arrow_length - px * self._arrow_perp
        righty = y_tip - ndy * self._arrow_length - py * self._arrow_perp
        _c = Color(*color)
        line1 = Line(points=[x_tip, y_tip, leftx, lefty], width=1.5)
        line2 = Line(points=[x_tip, y_tip, rightx, righty], width=1.5)
        self._arrow_head_refs.append({"line1": line1, "line2": line2, "color": _c})
