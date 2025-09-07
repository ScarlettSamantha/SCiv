import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple, Type

import numpy as np
from gameplay.resource import BaseResource
from system.subsystems.hexgen.edge import Edge
from system.subsystems.hexgen.enums import (
    Biome,
    GeoformType,
    Hemisphere,
    HexEdge,
    HexFeature,
    HexSide,
    HexType,
    MapType,
    Zones,
)
from system.subsystems.hexgen.territory import Territory

if TYPE_CHECKING:
    from system.subsystems.hexgen.grid import Grid


class Hex:
    def __init__(self, grid: "Grid", x: int, y: int, altitude: np.float64):
        self.x: int = x
        self.y: int = y
        self.altitude: np.float64 = altitude
        self.grid: "Grid" = grid

        self.edge_east = None
        self.edge_west = None
        self.edge_north_east = None
        self.edge_south_east = None
        self.edge_north_west = None
        self.edge_south_west = None

        self.princep_u = 0.0
        self.terrain: str = ""
        self.render_pos: Optional[Tuple[float, float]] = (0.0, 0.0)

        self.gameplay_resource: Optional[Type[BaseResource]] = None

        self.distance = 0  # distance in hexes to the coast. 0 if no coast
        self.moisture = 0.0

        self.territory: Optional[Territory] = None
        self.marked = False  # marked by the grouping algorithm

        self.bubble_cache: Dict[Any, Any] = dict()

        self.features: Set[Any] = set()

        # geoform type
        self.geoform_type: Optional[GeoformType] = None

        # geoform instance if it exists
        self.geoform: Optional[Any] = None

        self._neighbors: Optional[List[tuple[HexEdge, "Hex"]]] = None

        world_pressure = self.grid.params.get("surface_pressure", 1013.25)
        self.pressure: Tuple[float, float] = (float(world_pressure), float(world_pressure))

        # instance of a sea
        self.sea = None

        self.id = uuid.uuid4()

    def add_gameplay_resource(self, resource: Type[BaseResource]) -> None:
        self.gameplay_resource = resource

    def get_gameplay_resource(self) -> Type[BaseResource] | None:
        return self.gameplay_resource

    def has_feature(self, feature: HexFeature):
        """
        Does this hex have this feature
        :param feature: HexFeature
        :return:
        """
        return feature in self.features

    def add_feature(self, feature: HexFeature):
        """
        Adds a feature
        :param feature: HexFeature
        :return: None
        """
        self.features.add(feature)

    def remove_feature(self, feature: HexFeature):
        """
        Removes a feature
        :param feature: HexFeature
        :return: None
        """
        self.features.remove(feature)

    @property
    def is_owned(self):
        return self.territory is not None

    @property
    def latitude_ratio(self) -> float:
        ratio = self.x / self.grid.size
        if ratio < 0.5:
            ratio /= 0.5
        else:
            ratio = (1 - ratio) / 0.5
        return ratio

    @property
    def hemisphere(self) -> Hemisphere:
        if self.x <= round(self.grid.size / 2):
            return Hemisphere.northern
        return Hemisphere.southern

    @property
    def latitude(self) -> float:
        """Hex's current Latitude. Negative is south, positive is north"""
        ratio = self.x / self.grid.size
        if ratio < 0.5:  # north
            return (1 - ratio / 0.5) * 90
        else:  # south
            return ((ratio) / 0.5) * -90 + 90

    @property
    def zone(self) -> Zones:
        axial_tilt: float = float(abs(self.grid.params.get("axial_tilt", 18)))

        # northern polar zone
        northern_polar_zone: float = axial_tilt
        southern_polar_zone: float = -(0 - axial_tilt)
        northern_tropic_zone = axial_tilt
        southern_tropic_zone = -axial_tilt
        northern_temperate = axial_tilt + (axial_tilt / 2)
        southern_temperate = -(axial_tilt + (axial_tilt / 2))

        if northern_polar_zone < self.latitude <= 90:
            return Zones.arctic_circle
        elif northern_temperate < self.latitude <= northern_polar_zone:
            return Zones.northern_temperate
        elif northern_tropic_zone < self.latitude <= northern_temperate:
            return Zones.northern_subtropics
        elif 0 < self.latitude <= northern_tropic_zone:
            return Zones.northern_tropics
        elif southern_tropic_zone < self.latitude <= 0:
            return Zones.southern_tropics
        elif southern_temperate < self.latitude <= southern_tropic_zone:
            return Zones.southern_subtropics
        elif southern_polar_zone < self.latitude <= southern_temperate:
            return Zones.southern_temperate
        elif -90 < self.latitude <= southern_polar_zone:
            return Zones.antarctic_circle
        raise Exception("Zone invalid Latitude: {}".format(self.latitude))

    @property
    def base_temperature(self) -> tuple[float, float]:
        """
        Computes the temperature of this hex. Takes into account the latitude (x-coord) and
        the altitude (higher is colder)
        :return: number
        """
        # import ipdb; ipdb.set_trace()
        ratio = self.latitude_ratio
        avg_temp = self.grid.params.get("avg_temp", 10)
        volitility: float = round(abs(self.grid.params.get("axial_tilt", 18)))
        base_temp = self.grid.params.get("base_temp")
        min_temp: int = max(avg_temp - volitility, base_temp)
        # global avg temperature should be around ratio 0.4 and 0.6

        # part1 includes latitude only
        part1: float = (abs(min_temp) + (avg_temp + volitility)) * ratio + min_temp
        # return (part1, part1)
        # print(base_temp, avg_temp, volitility, min_temp, ratio, part1)
        #       43         73          16         57

        # part2 includes altitude
        factor: int = 7
        if self.is_water:
            factor = 8
        part2: float = abs(float(self.altitude) - self.grid.sealevel) / factor
        return (round(part1, 2) - round(part2, 2), round(part1, 2) - round(part2, 2))

    @property
    def temperature(self) -> tuple[float, float]:
        return (self.base_temperature[0], self.base_temperature[1])

    @property
    def biome(self) -> Biome:
        DESERT_TRANSITION_RAIN_THRESHOLD = 3.0
        GRASS_TO_FOREST_TRANSITION_THRESHOLD = 7.0
        RAIN_FOREST_THRESHOLD = 20.0
        FROST_LOWER_TEMP = 0.0
        FOREST_LOWER_TEMP = 5.0
        RAIN_FOREST_TEMPERATURE_THRESHOLD = 25.0

        map_type = self.grid.params.get("map_type")
        if map_type is not MapType.terran:
            return Biome.lifeless

        temp = self.temperature[0]
        rain = min(RAIN_FOREST_TEMPERATURE_THRESHOLD + 1, self.moisture)

        # 1) Extreme cold first (keep simple unless you have elevation/ice to split alpine vs arctic)
        if temp <= FROST_LOWER_TEMP:
            return Biome.arctic

        # 2) Wet/hot first so deserts don't steal them
        if rain >= RAIN_FOREST_THRESHOLD and temp >= RAIN_FOREST_TEMPERATURE_THRESHOLD:
            return Biome.tropical_rainforest
        if rain >= RAIN_FOREST_THRESHOLD and FOREST_LOWER_TEMP <= temp < RAIN_FOREST_TEMPERATURE_THRESHOLD:
            return Biome.temperate_rainforest

        # 3) Forest bands
        if (
            GRASS_TO_FOREST_TRANSITION_THRESHOLD <= rain < RAIN_FOREST_THRESHOLD
            and temp >= RAIN_FOREST_TEMPERATURE_THRESHOLD
        ):
            return Biome.tropical_forest
        if (
            GRASS_TO_FOREST_TRANSITION_THRESHOLD <= rain < RAIN_FOREST_THRESHOLD
            and FOREST_LOWER_TEMP <= temp < RAIN_FOREST_TEMPERATURE_THRESHOLD
        ):
            return Biome.temperate_forest
        if rain <= RAIN_FOREST_THRESHOLD and 0.0 < temp <= FOREST_LOWER_TEMP:
            return Biome.boreal_forest

        # 4) Grass/shrub/dry
        if DESERT_TRANSITION_RAIN_THRESHOLD <= rain <= GRASS_TO_FOREST_TRANSITION_THRESHOLD and 5.0 <= temp <= 30.0:
            return Biome.grasslands
        if 2.0 <= rain <= RAIN_FOREST_THRESHOLD and 0.0 < temp <= 10.0:
            return Biome.shrubland

        if 2.5 <= rain <= DESERT_TRANSITION_RAIN_THRESHOLD and 10.0 <= temp <= 40.0:
            return Biome.savanna
        if 0.0 <= rain <= DESERT_TRANSITION_RAIN_THRESHOLD and 10.0 < temp <= 40.0:
            return Biome.desert

        # 6) Tundra — keep your moisture cutoff but narrow temp a bit if tundra is too common
        if 0.0 <= rain and 0.0 < temp <= 10.0:
            return Biome.tundra

        raise Exception("Biome invalid Temp: {} Rain: {}".format(temp, rain))

    @property
    def max_size(self) -> int:
        return len(self.grid.grid) - 1

    @property
    def map_surrounding(self) -> list[Any]:
        """
        Returns the surrounding hexes without wrapping about the map
        :return: list of Hex
        """
        # east
        sur: List[Hex] = []
        if self.y != self.max_size:
            sur.append(self.grid.find_hex(self.x, self.y + 1))
        # west
        if self.y != 0:
            sur.append(self.grid.find_hex(self.x, self.y - 1))
        # north west
        if self.x != 0 and self.y != 0:
            if self.x % 2 == 0:  # even
                sur.append(self.grid.find_hex(self.x - 1, self.y - 1))
            else:
                sur.append(self.grid.find_hex(self.x - 1, self.y))
        # north east
        if self.x != 0 and self.y != self.max_size:
            if self.x % 2 == 0:  # even
                sur.append(self.grid.find_hex(self.x - 1, self.y))
            else:
                sur.append(self.grid.find_hex(self.x - 1, self.y + 1))
        # south west
        if self.x != self.max_size and self.y != 0:
            if self.x % 2 == 0:  # even
                sur.append(self.grid.find_hex(self.x + 1, self.y - 1))
            else:
                sur.append(self.grid.find_hex(self.x + 1, self.y))
        # south east
        if self.x != self.max_size and self.y != self.max_size:
            if self.x % 2 == 0:  # even
                sur.append(self.grid.find_hex(self.x + 1, self.y))
            else:
                sur.append(self.grid.find_hex(self.x + 1, self.y + 1))
        return sur

    @property
    def hex_east(self):
        """Returns the hex to the East or None if end of map"""
        if self.y == self.max_size:
            return self.grid.find_hex(self.x, 0)
        else:
            return self.grid.find_hex(self.x, self.y + 1)

    @property
    def hex_west(self):
        """Returns the hex to the West or None if end of map"""
        if self.y == 0:
            return self.grid.find_hex(self.x, self.max_size)
        else:
            return self.grid.find_hex(self.x, self.y - 1)

    @property
    def hex_north_west(self):
        """Returns the hex to the north west"""
        if self.x == 0:  # top of map
            return self.grid.find_hex(0, round(self.y / -1 + self.max_size))
        elif self.y == 0 and self.x % 2 == 0:  # left of map and even
            return self.grid.find_hex(self.x - 1, self.max_size)
        else:
            if self.x % 2 == 0:  # even
                return self.grid.find_hex(self.x - 1, self.y - 1)
            else:
                return self.grid.find_hex(self.x - 1, self.y)

    @property
    def hex_north_east(self):
        """Returns the hex to the North East or None if end of map"""
        if self.x == 0:  # top of map
            return self.grid.find_hex(0, round(self.y / -1 + self.max_size))
        elif self.y == self.max_size and self.x % 2 == 1:  # right of map and x is odd
            return self.grid.find_hex(self.x - 1, 0)
        else:
            if self.x % 2 == 0:  # even
                return self.grid.find_hex(self.x - 1, self.y)
            else:
                return self.grid.find_hex(self.x - 1, self.y + 1)

    @property
    def hex_south_west(self):
        """Returns the hex to the South West or None if end of map"""
        if self.x == self.max_size:  # bottom of map
            return self.grid.find_hex(self.max_size, round(self.y / -1 + self.max_size))
        elif self.y == 0 and self.x % 2 == 0:  # left of map and x is even
            return self.grid.find_hex(self.x + 1, self.max_size)
        else:
            if self.x % 2 == 0:  # even
                return self.grid.find_hex(self.x + 1, self.y - 1)
            else:
                return self.grid.find_hex(self.x + 1, self.y)

    @property
    def hex_south_east(self):
        """Returns the hex to the South East or None if end of map"""
        if self.x == self.max_size:  # bottom of map
            return self.grid.find_hex(self.max_size, round(self.y / -1 + self.max_size))
        elif self.y == self.max_size and self.x % 2 == 1:  # right of map and x is odd
            return self.grid.find_hex(self.x + 1, 0)
        else:
            if self.x % 2 == 0:  # even
                return self.grid.find_hex(self.x + 1, self.y)
            else:
                return self.grid.find_hex(self.x + 1, self.y + 1)

    def neighbor_at(self, direction: HexEdge) -> "Hex":
        """Given a HexEdge, find the hex on the other side of this edge"""
        if direction is HexEdge.east:
            return self.hex_east
        elif direction is HexEdge.south_east:
            return self.hex_south_east
        elif direction is HexEdge.south_west:
            return self.hex_south_west
        elif direction is HexEdge.west:
            return self.hex_west
        elif direction is HexEdge.north_west:
            return self.hex_north_west
        elif direction is HexEdge.north_east:
            return self.hex_north_east

    @property
    def surrounding(self) -> List["Hex"]:
        """
        Returns a list of all surrounding hexes
        Returns: Hex
        """
        return [
            self.hex_east,
            self.hex_south_east,
            self.hex_south_west,
            self.hex_west,
            self.hex_north_west,
            self.hex_north_east,
        ]

    @property
    def neighbors(self) -> List[tuple[HexEdge, "Hex"]]:
        """Surrounding hexes with HexEdge enums"""
        if self._neighbors is not None:
            return self._neighbors
        else:
            self._neighbors = [
                (HexEdge.east, self.hex_east),
                (HexEdge.south_east, self.hex_south_east),
                (HexEdge.south_west, self.hex_south_west),
                (HexEdge.west, self.hex_west),
                (HexEdge.north_west, self.hex_north_west),
                (HexEdge.north_east, self.hex_north_east),
            ]
            return self._neighbors

    def bubble(self, distance: int = 1) -> List["Hex"]:
        if distance == 0:
            return [self]
        elif distance == 1:
            return self.surrounding + [self]

        if distance in self.bubble_cache:
            return self.bubble_cache[distance]

        def step(iteration: int, hexes: List["Hex"]) -> List["Hex"]:
            if iteration < distance - 1:
                temp: List["Hex"] = []
                for h in hexes:
                    temp.extend(h.surrounding)
                return step(iteration + 1, temp)
            else:
                return hexes

        around: List["Hex"] = self.surrounding
        around.extend(step(0, around))
        final = list(set(around))
        self.bubble_cache[distance] = final
        return final

    @property
    def is_land(self) -> bool:
        """
        Determines whether or not this is a land hex. (Altitude over sealevel)
        :return: Boolean
        """
        return bool(self.altitude >= self.grid.sealevel)

    @property
    def is_water(self) -> bool:
        return self.is_land is False

    @property
    def type(self) -> HexType | HexType:
        if self.is_land:
            return HexType.land

        return HexType.ocean

    @property
    def is_inland(self) -> bool:
        if self.is_land is False:
            return False
        around = [
            self.hex_west,
            self.hex_east,
            self.hex_south_east,
            self.hex_south_west,
            self.hex_north_east,
            self.hex_north_west,
        ]
        return all(x.is_land for x in around)

    @property
    def is_coast_water(self) -> bool:
        return self.is_water and any(n.is_land for n in self.surrounding)

    @property
    def is_coast_land(self) -> bool:
        return self.is_land and any(n.is_water for n in self.surrounding)

    @property
    def is_coast(self) -> bool:
        return self.is_coast_water

    def decide_slope(self, one: "Hex", two: "Hex") -> tuple[Any, Any]:
        """Returns UP, DOWN tuple"""
        if one.altitude < two.altitude:
            return two, one
        return one, two

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Hex):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __key(self) -> tuple[int, int]:
        return self.x, self.y

    def __hash__(self) -> int:
        return hash(self.__key())

    @property
    def outer_edges(self) -> List[Any]:
        return [
            self.hex_north_east.edge_west,
            self.hex_north_west.edge_south_west,
            self.hex_west.edge_south_east,
            self.hex_south_west.edge_east,
            self.hex_south_east.edge_north_east,
            self.hex_east.edge_north_west,
        ]

    def calculate(self):
        """Calculate the edges"""
        h1 = self.hex_north_east
        h2 = self.hex_south_east
        up, down = self.decide_slope(h1, h2)
        self.edge_east = Edge(str(HexSide.east), self, self.hex_east, up, down)

        h1 = self.hex_north_west
        h2 = self.hex_south_west
        up, down = self.decide_slope(h1, h2)
        self.edge_west = Edge(str(HexSide.west), self, self.hex_west, up, down)

        h1 = self.hex_north_west
        h2 = self.hex_east
        up, down = self.decide_slope(h1, h2)
        self.edge_north_east = Edge(str(HexSide.north_east), self, self.hex_north_east, up, down)

        h1 = self.hex_south_west
        h2 = self.hex_east
        up, down = self.decide_slope(h1, h2)
        self.edge_south_east = Edge(str(HexSide.south_east), self, self.hex_south_east, up, down)

        h1 = self.hex_north_east
        h2 = self.hex_west
        up, down = self.decide_slope(h1, h2)
        self.edge_north_west = Edge(str(HexSide.north_west), self, self.hex_north_west, up, down)

        h1 = self.hex_south_east
        h2 = self.hex_west
        up, down = self.decide_slope(h1, h2)
        self.edge_south_west = Edge(str(HexSide.south_west), self, self.hex_south_west, up, down)

    def get_edge(self, side: HexSide) -> Edge | None:
        if side is HexSide.east:
            return self.edge_east
        elif side is HexSide.south_east:
            return self.edge_south_east
        elif side is HexSide.south_west:
            return self.edge_south_west
        elif side is HexSide.west:
            return self.edge_west
        elif side is HexSide.north_west:
            return self.edge_north_west
        elif side is HexSide.north_east:
            return self.edge_north_east

    @property
    def edges(self) -> List[Edge | None]:
        return [
            self.edge_east,
            self.edge_north_east,
            self.edge_north_west,
            self.edge_west,
            self.edge_south_west,
            self.edge_south_east,
        ]

    def __repr__(self):
        return "<HEX: X: {}, Y: {}, Z: {}>".format(self.x, self.y, self.altitude)

    def get_side_to(self, target_hex: "Hex") -> HexSide | None:
        for edge, neighbor in self.neighbors:
            if neighbor == target_hex:
                try:
                    return HexSide[edge.name]
                except KeyError:
                    return None
        return None
