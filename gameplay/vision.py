from typing import TYPE_CHECKING, List, Optional, Set

from gameplay.unit import Unit

if TYPE_CHECKING:
    from gameplay.city import City
    from gameplay.improvement import Improvement
    from gameplay.resource import BaseResource
    from gameplay.terrain._base_terrain import BaseTerrain
    from gameplay.tile import Tile


class Vision:
    def __init__(self):
        self._visible_tiles: Set[Tile] = set()
        self._visible_units: List[Unit] = []
        self._visible_cities: List[City] = []
        self._visible_resources: List[BaseResource] = []
        self._visible_improvements: List[Improvement] = []
        self._visible_terrain: List[BaseTerrain] = []

    def mass_set_visible_tiles(
        self,
        tiles: Optional[Set["Tile"]] = None,
        units: Optional[List["Unit"]] = None,
        cities: Optional[List["City"]] = None,
        resources: Optional[List["BaseResource"]] = None,
        improvements: Optional[List["Improvement"]] = None,
        terrain: Optional[List["BaseTerrain"]] = None,
    ):
        if tiles is not None:
            self._visible_tiles = set(tiles)
        if units is not None:
            self._visible_units = units
        if cities is not None:
            self._visible_cities = cities
        if resources is not None:
            self._visible_resources = resources
        if improvements is not None:
            self._visible_improvements = improvements
        if terrain is not None:
            self._visible_terrain = terrain

    def get_visible_tiles(self) -> Set["Tile"]:
        return self._visible_tiles

    def add_visible_tile(self, tile: "Tile"):
        self._visible_tiles.add(tile)

    def remove_visible_tile(self, tile: "Tile"):
        if tile in self._visible_tiles:
            self._visible_tiles.remove(tile)

    def get_visible_units(self) -> List["Unit"]:
        return self._visible_units

    def add_visible_unit(self, unit: "Unit"):
        if unit not in self._visible_units:
            self._visible_units.append(unit)

    def remove_visible_unit(self, unit: "Unit"):
        if unit in self._visible_units:
            self._visible_units.remove(unit)

    def get_visible_cities(self) -> List["City"]:
        return self._visible_cities

    def add_visible_city(self, city: "City"):
        if city not in self._visible_cities:
            self._visible_cities.append(city)

    def remove_visible_city(self, city: "City"):
        if city in self._visible_cities:
            self._visible_cities.remove(city)

    def get_visible_resources(self) -> List["BaseResource"]:
        return self._visible_resources

    def add_visible_resource(self, resource: "BaseResource"):
        if resource not in self._visible_resources:
            self._visible_resources.append(resource)

    def remove_visible_resource(self, resource: "BaseResource"):
        if resource in self._visible_resources:
            self._visible_resources.remove(resource)

    def get_visible_improvements(self) -> List["Improvement"]:
        return self._visible_improvements

    def add_visible_improvement(self, improvement: "Improvement"):
        if improvement not in self._visible_improvements:
            self._visible_improvements.append(improvement)

    def remove_visible_improvement(self, improvement: "Improvement"):
        if improvement in self._visible_improvements:
            self._visible_improvements.remove(improvement)

    def get_visible_terrain(self) -> List["BaseTerrain"]:
        return self._visible_terrain

    def add_visible_terrain(self, terrain: "BaseTerrain"):
        if terrain not in self._visible_terrain:
            self._visible_terrain.append(terrain)

    def remove_visible_terrain(self, terrain: "BaseTerrain"):
        if terrain in self._visible_terrain:
            self._visible_terrain.remove(terrain)
