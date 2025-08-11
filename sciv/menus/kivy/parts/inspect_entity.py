from functools import partial
from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional, Tuple, Union

from kivy.input.motionevent import MotionEvent
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.treeview import TreeView, TreeViewLabel
from direct.showbase import MessengerGlobal
from mixins.inspectable import Inspectable
from system.entity import BaseEntity

from gameplay.tile import Tile
from gameplay.unit import Unit


if TYPE_CHECKING:
    from managers.entity import BaseEntity
    from menus.screens.game_ui import GameUIScreen


class PlayersWrapper(Inspectable):
    def __init__(self, players: list["BaseEntity"]):
        self.name: str = "Players"
        self.players: list[BaseEntity] = players
        self.hidden_in_tree = True

    def __iter__(self) -> Iterator[BaseEntity]:
        return iter(self.players)

    def __getitem__(self, index: int) -> "BaseEntity":
        return self.players[index]

    def __len__(self) -> int:
        return len(self.players)

    def on_inspect(self) -> Tuple[Dict[str, Any], dict[str, Any]]:
        top_map: Dict[str, Any] = {}
        child_map: Dict[str, Any] = {}

        for player in self.players:
            if isinstance(player, Unit):
                top_map[str(player.name)] = player
            elif isinstance(player, Tile):
                top_map[str(player.name)] = player
            else:
                child_map.setdefault("Players", []).append(player)

        return top_map, child_map


class InspectEntity:
    def __init__(self, screen: "GameUIScreen"):
        self.screen: "GameUIScreen" = screen
        self.current_entity: Optional[Inspectable] = None
        self.is_open: bool = False

        self.frame: BoxLayout = BoxLayout(
            orientation="vertical", size_hint=(0.9, 0.9), pos_hint={"center_x": 0.5, "center_y": 0.5}
        )

        with self.frame.canvas.before:
            Color(0.7, 0.7, 0.7, 1)
            self._bg_rect = Rectangle(pos=self.frame.pos, size=self.frame.size)
        self.frame.bind(pos=self._update_bg, size=self._update_bg)

        self.header = Widget(size_hint_y=None, height=dp(30))
        with self.header.canvas.before:  # type: ignore
            Color(0, 0, 0, 1)
            self._header_rect = Rectangle(pos=self.header.pos, size=self.header.size)  # type: ignore
        self.header.bind(pos=self._update_header, size=self._update_header)

        self.content = BoxLayout(orientation="horizontal")

        self.left_container: BoxLayout = BoxLayout(orientation="vertical", size_hint_x=0.3)

        self.close_button = Button(text="Close", size_hint_y=None, height=dp(30))
        self.close_button.bind(on_release=lambda *_: MessengerGlobal.messenger.send("ui.update.ui.hide_inspect_ui"))

        self.divider: Widget = Widget(size_hint_x=None, width=dp(2))
        with self.divider.canvas:  # type: ignore
            Color(0.7, 0.7, 0.7, 1)
            self._divider_rect = Rectangle(pos=self.divider.pos, size=(self.divider.width, self.divider.height))  # type: ignore
        self.divider.bind(pos=self._update_divider, size=self._update_divider)

        self.right_container: GridLayout = GridLayout(
            cols=2,
            size_hint=(0.7, None),
            pos_hint={"top": 1},
        )
        self.right_container.bind(minimum_height=self.right_container.setter("height"))  # type: ignore

        self.footer = Widget(size_hint_y=None, height=dp(30))
        with self.footer.canvas.before:  #  type: ignore
            Color(0, 0, 0, 1)
            self._footer_rect = Rectangle(pos=self.footer.pos, size=self.footer.size)  #  type: ignore
        self.footer.bind(pos=self._update_footer, size=self._update_footer)

        self.frame.add_widget(self.header)
        self.content.add_widget(self.left_container)
        self.content.add_widget(self.divider)
        self.content.add_widget(self.right_container)
        self.frame.add_widget(self.content)
        self.frame.add_widget(self.footer)

        self.left_container.add_widget(Widget())  # spacer
        self.left_container.add_widget(self.close_button)

    def _update_bg(self, instance: BoxLayout, value: Any) -> None:
        self._bg_rect.pos = instance.pos
        self._bg_rect.size = instance.size

    def _update_header(self, instance: Widget, value: Any) -> None:
        self._header_rect.pos = instance.pos  #  type: ignore
        self._header_rect.size = instance.size

    def _update_footer(self, instance: Widget, value: Any) -> None:
        self._footer_rect.pos = instance.pos  #  type: ignore
        self._footer_rect.size = instance.size

    def _update_divider(self, instance: BoxLayout, value: Any) -> None:
        self._divider_rect.pos = instance.pos
        self._divider_rect.size = (instance.width, instance.height)

    def inspect_entity(self, entity: Inspectable) -> None:
        self.current_entity = entity
        self.left_container.clear_widgets()
        self.right_container.clear_widgets()

        _, top_map = entity.on_inspect()
        tree = TreeView(hide_root=True, size_hint=(1, 1))
        root_lbl = TreeViewLabel(text=self.make_entity_name(entity=entity))
        root_lbl.bind(on_touch_down=partial(self._on_tree_node_touch, entity))
        tree.add_node(root_lbl)  # type: ignore

        for key, descendants in top_map.items():
            if isinstance(key, Inspectable):
                self._build_entity_subtree(tree=tree, parent_node=root_lbl, ent=key)
            else:
                grp = TreeViewLabel(text=str(key))
                tree.add_node(grp, root_lbl)  # type: ignore
                for child in descendants:
                    self._build_entity_subtree(tree=tree, parent_node=grp, ent=child)

        self.left_container.add_widget(tree)
        self.left_container.add_widget(self.close_button)
        self._load_and_display_properties(entity)
        if not self.is_open:
            self.show()

    def make_entity_name(self, entity: Inspectable) -> str:
        if isinstance(entity, Tile):
            return f"({entity.__class__.__name__}) {entity.name} ({entity.x}, {entity.y})"
        if isinstance(entity, Unit):
            return f"({entity.get_owner().get_name_short()}) {entity.name}"
        if hasattr(entity, "name") and entity.name:  #  type: ignore
            return f"({entity.__class__.__name__}) {entity.name}"  #  type: ignore
        if hasattr(entity, "id"):
            return f"({entity.__class__.__name__}) {entity.id}"  # type: ignore
        return ""

    def _load_and_display_properties(self, entity: Union[Inspectable, str]) -> None:
        self.right_container.clear_widgets()
        if isinstance(entity, str):
            return

        for key, value in entity.on_inspect()[0].items():
            if key == "children":
                continue
            text = f"{key.capitalize() if key else 'None'}: " + str(value or "")
            label = Label(
                text=text,
                size_hint_y=None,
                halign="left",
                valign="middle",
                text_size=(self.right_container.width, None),  # type: ignore
                markup=True,
            )

            label.bind(width=lambda lbl, w: setattr(lbl, "text_size", (w, None)))  # type: ignore
            label.bind(texture_size=lambda lbl, ts: setattr(lbl, "height", ts[1]))  # type: ignore

            self.right_container.add_widget(label)

    def _build_entity_subtree(
        self,
        tree: TreeView,
        parent_node: TreeViewLabel,
        ent: Inspectable,
    ) -> None:
        node = TreeViewLabel(text=self.make_entity_name(ent))
        if ent.is_visible():
            tree.add_node(node=node, parent=parent_node)  # type: ignore
            node.bind(on_touch_down=partial(self._on_tree_node_touch, ent))
        _, child_map = ent.on_inspect()
        if not child_map:
            return
        for key, descendants in child_map.items():
            if isinstance(key, BaseEntity):
                self._build_entity_subtree(tree=tree, parent_node=node, ent=key)
            else:
                grp = TreeViewLabel(text=str(key))
                tree.add_node(grp, node)  # type: ignore
                for child in descendants:
                    self._build_entity_subtree(tree=tree, parent_node=grp, ent=child)

    def _on_tree_node_touch(
        self,
        entity: Inspectable,
        instance: TreeViewLabel,
        touch: MotionEvent,
    ) -> None:
        if instance.collide_point(*touch.pos):
            self._load_and_display_properties(entity)

    def show(self) -> None:
        self.frame.disabled = False
        self.frame.opacity = 1
        self.is_open = True

    def hide(self) -> None:
        self.frame.disabled = True
        self.frame.opacity = 0
        self.is_open = False
        self.current_entity = None
        self.left_container.clear_widgets()
        self.right_container.clear_widgets()
        MessengerGlobal.messenger.send("ui.update.ui.close_inspect_ui")
