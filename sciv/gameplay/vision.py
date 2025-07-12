from typing import TYPE_CHECKING, Any, List, Optional, Set, cast
from weakref import ReferenceType, ref

from gameplay.unit import Unit

if TYPE_CHECKING:
    from gameplay.city import City
    from gameplay.improvement import Improvement
    from gameplay.resource import BaseResource
    from gameplay.terrain._base_terrain import BaseTerrain
    from gameplay.tile import Tile


class Vision:
    def __init__(self):
        self._visible_tiles: Set[ReferenceType["Tile"]] = set()
        self._visible_units: List[ReferenceType["Unit"]] = []
        self._visible_cities: List[ReferenceType["City"]] = []
        self._visible_resources: List[ReferenceType["BaseResource"]] = []
        self._visible_improvements: List[ReferenceType["Improvement"]] = []
        self._visible_terrain: List[ReferenceType["BaseTerrain"]] = []

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
            self._visible_tiles = set([ref(tile) for tile in tiles])
        if units is not None:
            self._visible_units = [ref(unit) for unit in units]
        if cities is not None:
            self._visible_cities = [ref(city) for city in cities]
        if resources is not None:
            self._visible_resources = [ref(resource) for resource in resources]
        if improvements is not None:
            self._visible_improvements = [ref(improvement) for improvement in improvements]
        if terrain is not None:
            self._visible_terrain = [ref(terrain_item) for terrain_item in terrain]

    def get_visible_tiles(self) -> Set["Tile"]:
        tiles: Set["Tile"] = set()
        for tile in self._visible_tiles:
            if (resolved := tile()) is not None:
                tiles.add(resolved)
        return tiles

    def add_visible_tile(self, tile: "Tile"):
        self._visible_tiles.add(ref(tile))

    def remove_visible_tile(self, tile: "Tile"):
        if tile in self._visible_tiles:
            self._visible_tiles.remove(ref(tile))

    def get_visible_units(self) -> List["Unit"]:
        units: List["Unit"] = []
        for unit_ref in self._visible_units:
            if (resolved := unit_ref()) is not None:
                units.append(resolved)
        return units

    def add_visible_unit(self, unit: "Unit"):
        if unit not in self._visible_units:
            self._visible_units.append(ref(unit))

    def remove_visible_unit(self, unit: "Unit"):
        if unit in self._visible_units:
            self._visible_units.remove(ref(unit))

    def get_visible_cities(self) -> List["City"]:
        cities: List["City"] = []
        for city_ref in self._visible_cities:
            if (resolved := city_ref()) is not None:
                cities.append(resolved)
        return cities

    def add_visible_city(self, city: "City"):
        if city not in self._visible_cities:
            self._visible_cities.append(ref(city))

    def remove_visible_city(self, city: "City"):
        if city in self._visible_cities:
            self._visible_cities.remove(ref(city))

    def get_visible_resources(self) -> List["BaseResource"]:
        resources: List["BaseResource"] = []
        for resource_ref in self._visible_resources:
            if (resolved := resource_ref()) is not None:
                resources.append(resolved)
        return resources

    def add_visible_resource(self, resource: "BaseResource"):
        if resource not in self._visible_resources:
            self._visible_resources.append(ref(resource))

    def remove_visible_resource(self, resource: "BaseResource"):
        if resource in self._visible_resources:
            self._visible_resources.remove(ref(resource))

    def get_visible_improvements(self) -> List["Improvement"]:
        improvements: List["Improvement"] = []
        for improvement_ref in self._visible_improvements:
            if (resolved := improvement_ref()) is not None:
                improvements.append(resolved)
        return improvements

    def add_visible_improvement(self, improvement: "Improvement"):
        if improvement not in self._visible_improvements:
            self._visible_improvements.append(ref(improvement))

    def remove_visible_improvement(self, improvement: "Improvement"):
        if improvement in self._visible_improvements:
            self._visible_improvements.remove(ref(improvement))

    def get_visible_terrain(self) -> List["BaseTerrain"]:
        terrain: List["BaseTerrain"] = []
        for terrain_ref in self._visible_terrain:
            if (resolved := terrain_ref()) is not None:
                terrain.append(resolved)
        return terrain

    def add_visible_terrain(self, terrain: "BaseTerrain"):
        if terrain not in self._visible_terrain:
            self._visible_terrain.append(ref(terrain))

    def remove_visible_terrain(self, terrain: "BaseTerrain"):
        if terrain in self._visible_terrain:
            self._visible_terrain.remove(ref(terrain))

    def dump(self) -> List[str]:
        tiles: List[str] = []
        for tile in self._visible_tiles:
            if (resolved := tile()) is not None:
                tiles.append(resolved.get_tag())

        return tiles

    def load_state(self, state: List[str]) -> None:
        from managers.entity import EntityManager, EntityType

        self._visible_tiles = set()
        self._visible_units = []
        self._visible_cities = []
        self._visible_resources = []
        self._visible_improvements = []
        self._visible_terrain = []
        for tile_tag in state:
            tile_ref: ReferenceType["Tile"] | None = cast(
                ReferenceType["Tile"] | None,
                EntityManager.get_singleton_instance().get_ref_weak(EntityType.TILE, tile_tag),
            )
            if tile_ref is None:
                raise ValueError(f"Tile with tag {tile_tag} has been garbage collected.")
            tile: "Tile | None" = tile_ref()
            if tile is None:
                raise ValueError(f"Tile with tag {tile_tag} has been garbage collected.")

            self._visible_tiles.add(ref(tile))

            for unit in tile.get_units():
                self._visible_units.append(ref(unit))

            for improvement in tile.get_improvements():
                self._visible_improvements.append(ref(improvement))

            if tile.city is not None:
                self._visible_cities.append(ref(tile.city))

            self._visible_terrain.append(ref(tile.get_terrain()))

    def resolve_ref(self, refs: List[ReferenceType[Any]]) -> List[Any]:
        resolved: List[Any] = []
        for ref_item in refs:
            if (resolved_item := ref_item()) is not None:
                resolved.append(resolved_item)
        return resolved
