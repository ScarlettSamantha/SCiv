from collections import defaultdict
from typing import Any, Dict, List, Tuple, Type

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from kivy.graphics import Color, Line, Rectangle  # type: ignore
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout

from gameplay.tech import Tech, TechTree
from managers.player import PlayerManager
from managers.tech import TechManager
from managers.ui import ui
from menus.kivy.elements.horizontal_scroll import HorizontalScrollView
from menus.kivy.elements.tooltip import TooltippedButton


class ResearchButton(TooltippedButton):
    def __init__(self, value: Type[Tech], *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.value: Type[Tech] = value


class Research(FloatLayout, DirectObject):
    def __init__(self, tree: TechTree, **kwargs: Any) -> None:
        FloatLayout.__init__(self, **kwargs)  # type: ignore
        DirectObject.__init__(self, **kwargs)

        self.tree: TechTree = tree
        self.player_tech_manager: TechManager = PlayerManager.session_player().tech
        self._column_width: int = 350
        self._button_width: int = 180
        self._button_height: int = 60
        self._padding_left: int = 50
        self._vertical_spacing: int = 40
        self._box_margin: int = 10  # for routing around boxes if needed
        self._is_build: bool = False
        self.is_open: bool = False
        self.register()

    def register(self) -> None:
        self.accept("ui.update.ui.show_research_ui", self.show_popup)
        self.accept("ui.update.ui.hide_research_ui", self.hide_popup)
        self.accept("ui.update.ui.refresh_research_ui", self.update)
        self.accept_once("t", self.show_popup)

    def update(self, *args: Any) -> None:
        if self.is_open:
            self._calculate_button_state()

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

        self._float_layout = FloatLayout(size_hint=(None, 1), pos_hint={"top": 0, "y": 0})

        with self._float_layout.canvas.before:  # type: ignore
            Color(0.2, 0.2, 0.2, 0.8)  # dark gray background
            self._bg_rect = Rectangle(pos=self._float_layout.pos, size=self._float_layout.size)
        self._float_layout.bind(pos=self._update_rect, size=self._update_rect)  # type: ignore

        self.scroll_view.add_widget(self._float_layout)  # type: ignore

        self._tech_classes: List[Type[Tech]] = list(self.tree.items())  # type: ignore
        self._level_map: Dict[Type[Tech], int] = self._calculate_levels(self._tech_classes)

        self._buttons: Dict[Type[Tech], Button] = {}

        self._column_bounds: Dict[int, Tuple[float, float]] = {}

        self._tech_by_level: Dict[int, List[Type[Tech]]] = {}

        self._place_tech_buttons()
        self._draw_dependency_lines()
        self.add_widget(self.scroll_view)  # type: ignore
        self._is_build = True

    def _update_rect(self, instance: FloatLayout, value: Any) -> None:
        self._bg_rect.pos = instance.pos  # type: ignore
        self._bg_rect.size = instance.size  # type: ignore

    def _calculate_button_state(self) -> None:
        for btn in list(self._buttons.values()):  # type: ignore
            btn: ResearchButton = btn
            btn.disabled = self.player_tech_manager.is_tech_researched(
                btn.value
            ) or not self.player_tech_manager.are_tech_requirements_met(btn.value)
            if self.player_tech_manager.is_tech_researched(btn.value):
                btn.background_color = (0.0, 0.5, 0.0, 1)  # type: ignore
            elif type(self.player_tech_manager.researching) == btn.value:
                btn.background_color = (0, 0, 0.5, 1)  # type: ignore
            else:
                btn.background_color = (0.5, 0.5, 0.5, 0.7)  # type: ignore

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

        max_count = max((len(lst) for lst in sorted_tech_by_level.values()), default=1)
        total_height = max_count * self._button_height + (max_count + 1) * self._vertical_spacing

        for level, tech_list in sorted_tech_by_level.items():
            n = len(tech_list)
            spacing = (total_height - n * self._button_height) / (n + 1) if n > 0 else 0

            col_min_y = float("inf")
            col_max_y = float("-inf")

            for i, tech_cls in enumerate(tech_list):
                x_pos = self._padding_left + level * self._column_width + (self._column_width - self._button_width) / 2
                y_pos = spacing * (i + 1) + i * self._button_height

                btn = ResearchButton(
                    text=f"{str(tech_cls.name)}({str(tech_cls.tech_points_required)})",
                    tooltip_text=str(tech_cls.description),
                    size_hint=(None, None),
                    size=(self._button_width, self._button_height),
                    pos=(x_pos, y_pos),
                    value=tech_cls,
                )
                btn.disabled = self.player_tech_manager.is_tech_researched(
                    tech_cls
                ) or not self.player_tech_manager.are_tech_requirements_met(tech_cls)

                btn.bind(on_release=self.on_research_button_click)  # type: ignore

                self._float_layout.add_widget(btn)  # type: ignore
                self._buttons[tech_cls] = btn

                top_y = y_pos + self._button_height
                col_min_y = min(col_min_y, y_pos)
                col_max_y = max(col_max_y, top_y)

            self._column_bounds[level] = (col_min_y, col_max_y)

        max_level = max(self._level_map.values()) if self._level_map else 0
        self._float_layout.width = (max_level + 1) * self._column_width + self._padding_left * 2
        self._float_layout.height = total_height
        self._calculate_button_state()

    def on_research_button_click(self, btn: ResearchButton) -> None:
        MessengerGlobal.messenger.send("game.gameplay.research.request_start_research_session_player", [btn.value])
        MessengerGlobal.messenger.send("ui.update.ui.refresh_research_ui")

    def _draw_dependency_lines(self, *args: Any) -> None:
        if not self._buttons or not self._float_layout.canvas:
            return

        with self._float_layout.canvas.before:
            Color(1, 1, 1)
            for tech_cls in self._tech_classes:
                if tech_cls not in self._buttons:
                    continue
                to_btn = self._buttons[tech_cls]
                tgt_level = self._level_map[tech_cls]

                for req_cls in tech_cls.requires:
                    from_btn = self._buttons.get(req_cls)
                    if not from_btn:
                        continue
                    sx, sy = from_btn.right, from_btn.center_y
                    src_level = self._level_map[req_cls]
                    points = self._build_stepwise_path(src_level, tgt_level, sx, sy, to_btn)
                    # Draw main line
                    Color(1, 1, 1, 1)
                    Line(points=points, width=1.5)
                    # Draw arrowhead
                    self._draw_arrowhead(points)

    def _get_route_y_for_column(self, col: int, current_y: float, target_y: float) -> float:
        """
        Decide a vertical route for lines in each column to avoid collisions with buttons.
        """
        if col not in self._tech_by_level:
            return current_y

        centers: List[float] = []
        for tech_cls in self._tech_by_level[col]:
            btn = self._buttons.get(tech_cls)
            if btn:
                centers.append(btn.center_y)
        if not centers:
            return current_y

        centers.sort()
        n = len(centers)
        if n % 2 == 0:
            # Even number: route through the gap between the two central buttons
            route_y = (centers[n // 2 - 1] + centers[n // 2]) / 2.0
        else:
            # Odd: shift up/down from the center button
            mid = centers[n // 2]
            offset = (self._button_height / 2) + (self._vertical_spacing / 2)
            route_y = mid - offset if target_y < mid else mid + offset
        return route_y

    def _build_stepwise_path(self, src_level: int, tgt_level: int, sx: float, sy: float, to_btn: Button) -> List[float]:
        """
        Build a list of (x,y) points forming a stepwise path from (sx, sy) to 'to_btn',
        using 90-degree angles. For directly adjacent columns, we simplify the path.
        """
        # If the source and target columns differ by exactly 1, make a single L-shaped path.
        if abs(tgt_level - src_level) == 1:
            points: List[float] = [sx, sy]

            # Are we going left->right or right->left?
            going_right = tgt_level > src_level
            if going_right:
                # 1) horizontal from from_btn.right to just before target's x
                mid_x: int = to_btn.x - 30  # type: ignore
            else:
                # 1) horizontal from from_btn.x to just after target's right
                mid_x: int = to_btn.right + 10

            # Horizontal leg
            points.extend([mid_x, sy])  # type: ignore
            # Vertical leg
            points.extend([mid_x, to_btn.center_y])  # type: ignore

            # Final small horizontal to the target’s actual x (left->right) or right (right->left)
            final_x = to_btn.x if going_right else to_btn.right  # type: ignore
            points.extend([final_x, to_btn.center_y])  # type: ignore

            return points

        # Otherwise, use the multi-step route for multi-column hops.
        points: List[float] = [sx, sy]
        current_x, current_y = sx, sy
        step = 1 if tgt_level >= src_level else -1
        col = src_level

        while col != tgt_level:
            next_col = col + step
            if step > 0:
                # move to the next column boundary on the left
                boundary_x = (
                    self._padding_left + next_col * self._column_width - 20  # keep it a bit away from the button
                )
            else:
                # move to the next column boundary on the right
                boundary_x = self._padding_left + next_col * self._column_width + self._button_width + 20

            # Horizontal step
            if abs(boundary_x - current_x) > 1e-6:
                points.extend([boundary_x, current_y])
                current_x = boundary_x

            # Vertical routing to avoid collisions
            ideal_y = self._get_route_y_for_column(next_col, current_y, to_btn.center_y)
            if abs(ideal_y - current_y) > 1e-6:
                points.extend([current_x, ideal_y])
                current_y = ideal_y

            col = next_col

        # Final approach to the target button
        final_x = to_btn.x if tgt_level >= src_level else to_btn.right  # type: ignore
        if abs(to_btn.center_y - current_y) > 1e-6:
            points.extend([current_x, to_btn.center_y])
            current_y = to_btn.center_y
        if abs(final_x - current_x) > 1e-6:  # type: ignore
            points.extend([final_x, current_y])  # type: ignore

        return points

    def _draw_arrowhead(self, points: List[float]) -> None:
        if len(points) < 4:
            return

        x_prev, y_prev = points[-4], points[-3]
        x_last, y_last = points[-2], points[-1]

        dx, dy = x_last - x_prev, y_last - y_prev
        dist = (dx * dx + dy * dy) ** 0.5
        if dist < 1e-6:
            return

        # Unit direction
        ndx, ndy = dx / dist, dy / dist

        # Pull the line end back a bit
        back_offset = 40
        line_end_x = x_last - ndx - back_offset
        line_end_y = y_last - ndy - back_offset

        # Replace the final coordinate in the line
        points[-2], points[-1] = line_end_x, line_end_y

        # Tip (still at x_last, y_last) – we’ll offset it slightly if needed
        tipx, tipy = x_last - 5, y_last

        arrow_length = 12
        perp_len = 4
        spacing_arrow_points = 5

        leftx = tipx - (ndx * arrow_length) + (ndy * perp_len)
        lefty = tipy - (ndy * arrow_length) - (ndx * perp_len) - spacing_arrow_points
        rightx = tipx - (ndx * arrow_length) - (ndy * perp_len)
        righty = tipy - (ndy * arrow_length) + (ndx * perp_len) + spacing_arrow_points

        # Two lines for the arrowhead
        Color(1, 1, 1, 1)
        Line(points=[tipx, tipy, leftx, lefty], width=1.5)
        Line(points=[tipx, tipy, rightx, righty], width=1.5)

    def show_popup(self, *_: Any) -> None:
        is_escape_open = ui.get_singleton_instance().get_screen("pause_menu").pause_menu._is_open  # type: ignore
        if is_escape_open:  # We check if we are in the game screen
            self.accept_once(
                "t", self.show_popup
            )  # This is to re-accept the t key if a popup is not shown so we don't get stuck
            return

        if self._is_build is False:
            self.build()
        self.opacity = 1
        self.disabled = False
        self.accept_once("t", self.hide_popup)
        MessengerGlobal.messenger.send("system.input.raycaster_off")
        MessengerGlobal.messenger.send("system.input.disable_zoom")
        MessengerGlobal.messenger.send("system.input.disable_control")
        MessengerGlobal.messenger.send("system.input.camera_lock")
        self.is_open = True

    def hide_popup(self, *_: Any) -> None:
        self.clear_widgets()
        self._is_build = False
        self.accept_once("t", self.show_popup)
        MessengerGlobal.messenger.send("system.input.camera_unlock")
        MessengerGlobal.messenger.send("system.input.raycaster_on")
        MessengerGlobal.messenger.send("system.input.enable_zoom")
        MessengerGlobal.messenger.send("system.input.enable_control")
        self.is_open = False
