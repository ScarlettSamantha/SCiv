import math
from typing import Any, Dict, List, Optional, Tuple, Type

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from kivy.app import Widget
from kivy.graphics import Color, Line, Rectangle, Triangle  # type: ignore
from kivy.uix.anchorlayout import AnchorLayout  # NEW
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label

from gameplay.civic import Civic, CivicSubtree, CivicTree
from gameplay.civics.core.tree.core import CoreCivicTree
from helpers.placeholder import Placeholder
from managers.ui import ui
from menus.kivy.elements.horizontal_scroll import HorizontalScrollView
from menus.kivy.elements.tooltip import TooltipBehavior


class CivicNode(ButtonBehavior, AnchorLayout, TooltipBehavior):
    def __init__(self, civic: Type[Civic], icon_px: int = 64, **kwargs: Any):
        TooltipBehavior.__init__(self, **kwargs)
        super().__init__(size_hint=(None, None), size=(icon_px + 4, icon_px + 4), **kwargs)  # type: ignore

        self.civic = civic
        _civic = civic()

        icon_src = getattr(_civic, "icon_path", Placeholder.getPlaceholderImagePathSmallIcon())
        name = str(getattr(_civic, "name", ""))
        description = str(getattr(_civic, "description", ""))
        cost = _civic.get_cost()

        unlocks = civic.get_unlocks()
        requires = civic.get_requirements()

        def civic_name_list(cls_list: List[Type[Civic]]) -> str:
            return "\n".join(f"• {getattr(_cls(), 'name', str(_cls))}" for _cls in cls_list)

        tooltip_parts = [
            f"[b]{name}[/b]",
            "",
            description,
            "",
        ]

        if unlocks:
            tooltip_parts.append("[b]Unlocks:[/b]")
            tooltip_parts.append(civic_name_list(unlocks))
            tooltip_parts.append("")

        if requires:
            tooltip_parts.append("[b]Requires:[/b]")
            tooltip_parts.append(civic_name_list(requires))
            tooltip_parts.append("")

        tooltip_parts.append(f"[b]Cost:[/b] {cost}")
        self.tooltip_text = "\n".join(tooltip_parts)
        self.tooltip_markup = True
        self.tooltip_image_source = icon_src
        self.tooltip_multiline = True

        # Background and Icon
        with self.canvas.before:
            self.bg_color = Color(0.3, 0.3, 0.3, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)  # type: ignore
        self.bind(pos=self._update_rect, size=self._update_rect)
        self.bind(state=self._on_state_change)  # type: ignore

        self.icon = Image(source=icon_src, size_hint=(None, None), size=(icon_px, icon_px))
        self.add_widget(self.icon)

    def _update_rect(self, *args: Any):
        self.bg_rect.pos = self.pos  # type: ignore
        self.bg_rect.size = self.size

    def _update_label(self, instance: Label, size: List[int]) -> None:
        instance.text_size = size

    def _on_state_change(self, instance: "CivicNode", value: str):
        if value == "down":
            self.bg_color.rgba = (0.2, 0.2, 0.2, 1)
        else:
            self.bg_color.rgba = (0.3, 0.3, 0.3, 1)


class SubtreeCard(BoxLayout):
    def __init__(self, subtree: Type[CivicSubtree], civic_node_map: Dict[Type[Civic], CivicNode], **kwargs: Any):
        super().__init__(
            orientation="vertical",
            padding=10,
            spacing=10,
            size_hint=(None, 0.35),
            width=335,
            **kwargs,  # type: ignore
        )

        # ---------- background ----------
        with self.canvas.before:
            Color(0.4, 0.4, 0.4, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)  # type: ignore
        self.bind(pos=self._update_rect, size=self._update_rect)

        # ---------- title ----------
        title = Label(text=subtree.__name__, size_hint=(1, None), height=30, halign="center", valign="middle")
        title.bind(size=self._update_label)  # type: ignore
        self.add_widget(title)

        # ---------- build rows exactly as before ----------
        civics = subtree.register_civics()
        tiers = self._group_by_tier(civics)

        node_w = node_h = 72
        row_spacing = 24
        col_spacing = 24

        rows_box = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),  # full width
            spacing=row_spacing,
        )

        for tier in sorted(tiers):
            row = BoxLayout(orientation="horizontal", size_hint=(None, None), spacing=col_spacing)

            civics_in_row = tiers[tier]
            row.width = len(civics_in_row) * node_w + (len(civics_in_row) - 1) * col_spacing
            row.height = node_h

            # centre row inside the fixed‑width card
            anchor = AnchorLayout(size_hint=(1, None), height=node_h)
            anchor.add_widget(row)
            rows_box.add_widget(anchor)

            for civic in civics_in_row:
                node = CivicNode(civic, icon_px=64)
                civic_node_map[civic] = node
                row.add_widget(node)

        rows_box.height = len(tiers) * node_h + (len(tiers) - 1) * row_spacing

        # occupy remaining space, keep centred
        main_anchor = AnchorLayout(size_hint=(1, 1), anchor_x="center", anchor_y="center")
        main_anchor.add_widget(rows_box)
        self.add_widget(main_anchor)

    # --------------------------------------------------------
    # helpers
    # --------------------------------------------------------
    def _group_by_tier(self, civics: List[Type[Civic]]) -> Dict[int, List[Type[Civic]]]:
        tiers: Dict[int, List[Type[Civic]]] = {}
        for civic in civics:
            tier = civic.get_tier()
            if tier not in tiers:
                tiers[tier] = []
            tiers[tier].append(civic)
        return tiers

    # ------------------------------------------------------------------ #
    # canvas helpers
    # ------------------------------------------------------------------ #
    def _update_rect(self, *args: Any):
        self.bg_rect.pos = self.pos  # type: ignore
        self.bg_rect.size = self.size

    def _update_label(self, instance: Label, size: List[int]) -> None:
        instance.text_size = size


class Civics(FloatLayout, DirectObject):
    def __init__(self, tree: CivicTree, **kwargs: Any) -> None:
        FloatLayout.__init__(self, **kwargs)
        DirectObject.__init__(self, **kwargs)

        self._is_build: bool = False
        self.is_open: bool = False
        self.tree: CoreCivicTree = tree if isinstance(tree, CoreCivicTree) else CoreCivicTree()
        self.civic_node_map: Dict[Type[Civic], CivicNode] = {}
        self._float_layout: Optional[FloatLayout] = None
        self.layout: Optional[GridLayout] = None
        self.scroll_view: Optional[HorizontalScrollView] = None

        self.register()

    # ------------------------------------------------------------------ #
    # event registration
    # ------------------------------------------------------------------ #
    def register(self) -> None:
        self.accept("ui.update.ui.show_civic_ui", self.show_popup)
        self.accept("ui.update.ui.hide_civic_ui", self.hide_popup)
        self.accept("ui.update.ui.refresh_civic_ui", self.update)
        self.accept_once("c", self.show_popup)

    # ------------------------------------------------------------------ #
    # lifecycle
    # ------------------------------------------------------------------ #
    def update(self, *args: Any) -> None:
        if not self._is_build:
            self.build()

        self.layout.clear_widgets()  # type: ignore
        self.civic_node_map.clear()

        self.tree.register_subtrees()
        subtrees = self.tree.get_all_subtrees()
        subtrees.sort(key=lambda subtree: getattr(subtree, "order", float("inf")))

        for subtree in subtrees:
            col = SubtreeCard(subtree, self.civic_node_map)
            self.layout.add_widget(col)  # type: ignore

        # defer line drawing to next frame
        # Clock.schedule_once(lambda dt: self.draw_dependency_lines(), 0.25)  # type: ignore

    def build(self) -> None:
        if self._is_build:
            return

        # full‑screen horizontal scroll area
        self.scroll_view = HorizontalScrollView(
            do_scroll_x=True,
            do_scroll_y=False,
            scroll_type=["bars", "content"],
            bar_width=15,
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )

        self.layout = GridLayout(
            rows=2,
            orientation="lr-tb",
            spacing=40,
            padding=[40, 40, 40, 40],
            size_hint=(None, 1),
        )
        self.layout.bind(minimum_width=self.layout.setter("width"))  # type: ignore

        # background
        with self.canvas.before:  # type: ignore
            Color(0.2, 0.2, 0.2, 1)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)  # type: ignore
        self.bind(pos=self._update_rect, size=self._update_rect)

        self.scroll_view.add_widget(self.layout)  # type: ignore
        self.add_widget(self.scroll_view)

        self._is_build = True

    # ------------------------------------------------------------------ #
    # drawing / dependency lines
    # ------------------------------------------------------------------ #
    def draw_dependency_lines(self) -> None:
        """
        Draw arrows from each civic to the ones it unlocks,
        assuming civics are in a two-row layout:
            - Arrows go from bottom of top-row nodes to top of bottom-row nodes.
        """

        def get_relative_pos(widget: Widget, ancestor: Widget) -> Tuple[int, int] | Tuple[int | float, int | float]:
            pos = widget.center
            current = widget
            while current is not ancestor:
                pos = current.to_parent(*pos, relative=True)  # type: ignore
                current = current.parent
            return pos  # type: ignore

        self.canvas.after.clear()  # type: ignore
        with self.canvas.after:  # type: ignore
            Color(1, 1, 0, 0.7)  # yellow
            arrow_size = 8

            for civic, node in self.civic_node_map.items():
                for unlocked in civic.get_unlocks():
                    if unlocked in self.civic_node_map:
                        src_node = node
                        dst_node = self.civic_node_map[unlocked]

                        # Bottom center of source node
                        src = get_relative_pos(src_node, self)
                        src = (src[0], src[1] - src_node.height / 2)  # type: ignore

                        # Top center of destination node
                        dst = get_relative_pos(dst_node, self)
                        dst = (dst[0], dst[1] + dst_node.height / 2)  # type: ignore

                        # Draw arrow shaft
                        Line(points=[*src, *dst], width=2)

                        # Draw arrowhead at destination
                        dx, dy = dst[0] - src[0], dst[1] - src[1]  # type: ignore
                        length = math.hypot(dx, dy) or 1  # type: ignore
                        ux, uy = dx / length, dy / length  # type: ignore
                        px, py = -uy, ux  # perpendicular vector # type: ignore

                        p1 = (  # type: ignore
                            dst[0] - ux * arrow_size + px * arrow_size * 0.5,
                            dst[1] - uy * arrow_size + py * arrow_size * 0.5,
                        )
                        p2 = (  # type: ignore
                            dst[0] - ux * arrow_size - px * arrow_size * 0.5,
                            dst[1] - uy * arrow_size - py * arrow_size * 0.5,
                        )

                        Triangle(points=[dst[0], dst[1], *p1, *p2])

    # ------------------------------------------------------------------ #
    # geometry helpers
    # ------------------------------------------------------------------ #
    def _update_rect(self, *args: Any) -> None:
        self._bg_rect.pos = self.pos  # type: ignore
        self._bg_rect.size = self.size

    def show_popup(self, *_: Any) -> None:
        is_escape_open = ui.get_singleton_instance().get_screen("pause_menu").pause_menu._is_open  # type: ignore
        if is_escape_open:
            self.accept_once("c", self.show_popup)
            return

        if not self._is_build:
            self.build()
        self.update()
        self.opacity = 1
        self.disabled = False
        self.popup_disabled = False
        self.accept_once("c", self.hide_popup)
        MessengerGlobal.messenger.send("system.input.raycaster_off")
        MessengerGlobal.messenger.send("system.input.disable_zoom")
        MessengerGlobal.messenger.send("system.input.disable_control")
        MessengerGlobal.messenger.send("system.input.camera_lock")
        self.is_open = True

    def hide_popup(self, *_: Any) -> None:
        self.clear_widgets()
        self._is_build = False
        self.popup_disabled = True
        self.accept_once("c", self.show_popup)
        self.opacity = 0
        self.disabled = True
        MessengerGlobal.messenger.send("system.input.camera_unlock")
        MessengerGlobal.messenger.send("system.input.raycaster_on")
        MessengerGlobal.messenger.send("system.input.enable_zoom")
        MessengerGlobal.messenger.send("system.input.enable_control")
        self.is_open = False
