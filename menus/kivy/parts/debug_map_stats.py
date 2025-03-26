import copy
from logging import Logger
from typing import TYPE_CHECKING, Dict, Optional, Tuple, Type

from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label

from gameplay.resource import BaseResource, ResourceSpawnablePlace
from helpers.colors import Colors
from managers.game import World

if TYPE_CHECKING:
    from gameplay.tiles.base_tile import BaseTile


class DebugMapStats(FloatLayout):
    def __init__(self, base, logger: Logger, offset=10, **kwargs):
        self.logger = logger
        super().__init__(**kwargs)
        self.base = base
        self.offset = offset  # Fixed pixel offset from the top

        self.frame = None
        self.map_resource_column: Optional[Label] = None
        self.map_type_column: Optional[Label] = None
        self.loaded_resources: Dict[str, Type["BaseResource"]] = {}
        self.rect = None

        self.map: Dict[str, "BaseTile"] = World.get_instance().map

    def get_frame(self) -> GridLayout:
        if self.frame is None:
            self.frame = self.build()
        return self.frame

    def _calculate_map_stats(self) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float], Dict[str, float]]:
        self.map = World.get_instance().map
        running_total_resources: Dict[str, float] = {}
        running_total_tile_type: Dict[str, float] = {}
        total_tiles: int = len(self.map)  # Total number of tiles in the map
        self.loaded_resources: Dict[str, Type["BaseResource"]] = {}

        # Sum resource counts over all tiles
        for tile in self.map.values():
            for resource in tile.resources:
                running_total_resources[resource.key] = running_total_resources.get(resource.key, 0) + 1.0
                if resource.__class__ not in list(self.loaded_resources.values()):
                    self.loaded_resources[resource.key] = resource.__class__

            running_total_tile_type[str(tile._tile_terrain.name)] = (
                running_total_tile_type.get(str(tile._tile_terrain.name), 0) + 1.0
            )

        # Divide each resource's total by the number of tiles to get the average
        total_resources = copy.deepcopy(running_total_resources)
        for key in running_total_resources:
            running_total_resources[key] /= total_tiles

        total_tiles_types = copy.deepcopy(running_total_tile_type)
        for key in running_total_tile_type:
            running_total_tile_type[key] /= total_tiles

        return running_total_resources, running_total_tile_type, total_resources, total_tiles_types

    def update(self):
        if self.map_resource_column is None or self.map_type_column is None:
            return

        resource_stats, tile_type_stats, resource_total, tile_total = self._calculate_map_stats()

        # Convert stats to list of tuples and sort by value in descending order
        sorted_stats_resources = sorted(resource_stats.items(), key=lambda x: x[1], reverse=True)
        sorted_stats_tile_type = sorted(tile_type_stats.items(), key=lambda x: x[1], reverse=True)

        # Format each line and join them
        formatted_lines = []
        for key, value in sorted_stats_resources:
            # Extract the part after second dot
            simplified_key = key.split(".")[2:]
            color_hex = Colors.to_hex(self.loaded_resources[key]._color)  # type: ignore
            simplified_key = rf"[color={color_hex.upper()}][[{simplified_key[0][0]}]]{
                simplified_key[1]
            }[/color]"  # First letter of the first part so b for bonus, l for luxury, s for strategic

            # Convert to percentage with 2 decimal places
            percentage = round(value * 100, 2)
            color = Colors.to_hex(Colors.WHITE, strip_alpha=True)
            if self.loaded_resources[key].spawn_type == ResourceSpawnablePlace.WATER:
                color = Colors.to_hex(Colors.BLUE, strip_alpha=True)
            elif self.loaded_resources[key].spawn_type == ResourceSpawnablePlace.LAND:
                color = Colors.to_hex(Colors.GREEN, strip_alpha=True)
            elif self.loaded_resources[key].spawn_type == ResourceSpawnablePlace.BOTH:
                color = Colors.to_hex(Colors.PURPLE, strip_alpha=True)
            formatted_lines.append(
                f"{simplified_key}: {percentage}%[color={color}][@{int(resource_total[key])}][/color]"
            )

        text = "\n".join(formatted_lines)
        self.map_resource_column.text = text

        formatted_lines = []
        for key, value in sorted_stats_tile_type:
            simplified_key = key.split(".")[-1]
            # Convert to percentage with 2 decimal places
            percentage = round(value * 100, 2)
            formatted_lines.append(f"{simplified_key}: {percentage}%[@{int(tile_total[key])}]")

        text = "\n".join(formatted_lines)
        self.map_type_column.text = text

    def build(self) -> GridLayout:
        # --- Debug Panel (Mid-Left Corner) ---
        self.frame = GridLayout(
            size_hint=(None, None),
            cols=2,
            rows=1,
            width=300,
            height=600,
            pos_hint={"left": 1, "top": 0.45},
        )

        with self.frame.canvas.before:  # type: ignore
            Color(0, 0, 0, 0.7)  # Black background with 70% opacity
            self.rect = Rectangle(size=self.frame.size, pos=self.frame.pos)

        def update_debug_rect(instance, value):
            self.rect.size = instance.size  # type: ignore
            self.rect.pos = instance.pos  # type: ignore

        self.frame.bind(size=update_debug_rect, pos=update_debug_rect)  # type: ignore

        self.map_resource_column = Label(
            text="?",
            size_hint=(None, None),
            width=165,
            height=600,
            font_size="11sp",
            valign="top",
            halign="left",
            text_size=(165, 600),
            pos_hint={"left": 1, "top": 1},
            color=(1, 1, 1, 1),
            padding=2,
            markup=True,
        )

        self.map_type_column = Label(
            text="?",
            size_hint=(None, None),
            width=125,
            height=600,
            font_size="11sp",
            valign="top",
            halign="left",
            text_size=(125, 600),
            pos_hint={"left": 1, "top": 1},
            color=(1, 1, 1, 1),
            padding=2,
            markup=True,
        )

        self.frame.add_widget(self.map_resource_column)
        self.frame.add_widget(self.map_type_column)
        return self.frame

    def update_debug_info(self, text: str):
        if self.map_resource_column is None:
            return

        self.map_resource_column.text = text
