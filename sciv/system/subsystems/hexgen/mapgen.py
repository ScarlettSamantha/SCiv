import datetime
import random
import sys
from typing import Any, Dict, List, Set, Tuple
from matplotlib.patches import RegularPolygon
import numpy as np
import matplotlib.pyplot as plt
from helpers.debug import Debug as DebugHelper
from system.subsystems.hexgen.hex import Hex
from system.subsystems.hexgen.enums import (
    GeoformType,
    HexFeature,
    MapType,
    OceanType,
)
from system.subsystems.hexgen.geoform import Geoform
from system.subsystems.hexgen.grid import Grid
from system.subsystems.hexgen.heightmap import Heightmap
from system.subsystems.hexgen.hex import HexSide
from system.subsystems.hexgen.river import RiverSegment
from system.subsystems.hexgen.territory import Territory
from system.subsystems.hexgen.util import (
    Timer,
    first_hex_without_geoform,
    is_bay,
    is_isthmus,
    is_peninsula,
    is_strait,
)

sys.setrecursionlimit(10000000)

default_params: Dict[str, Any] = {
    "map_type": MapType.terran,
    "surface_pressure": 1013.25,
    "size": 100,
    "base_temp": 0,
    "avg_temp": 15,
    "sea_percent": 60,
    "hydrosphere": True,
    "ocean_type": OceanType.water,
    "random_seed": None,
    "roughness": 8,
    "height_range": (0, 255),
    "pressure": 1,  # bar
    "axial_tilt": 23,
    # features
    "craters": False,
    "volcanoes": True,
    "num_volcanoes": 5,
    "volcano_area_size": 1,
    "num_rivers": 50,
    # territories
    "num_territories": 0,
}


class MapGen:
    """generates a heightmap as an array of integers between 1 and 255
    using the diamond-square algorithm"""

    def __init__(self, params: Dict[str, Any], debug: bool = False):
        """initialize"""
        self.params: Dict[str, Any] = default_params
        self.params.update(params)

        self.debug = DebugHelper.world_generation()

        if type(params.get("random_seed")) is int:
            random.seed(params.get("random_seed"))

        with Timer("Building Heightmap", self.debug):
            self.heightmap = Heightmap(self.params, self.debug)

        self.hex_grid: Grid = Grid(self.heightmap, self.params)
        if self.debug is True:
            print("\tAverage Height: {}".format(self.hex_grid.average_height))
            print("\tHighest Height: {}".format(self.hex_grid.highest_height))
            print("\tLowest Height: {}".format(self.hex_grid.lowest_height))

        self.rivers: List[Any] = []
        self.rivers_sources: List[RiverSegment] = []

        with Timer("Computing hex distances", self.debug):
            self._get_distances()

        self.num_tiles: int = 0

        if self.params.get("hydrosphere"):
            self._generate_rivers()

            print("Making coastal moisture") if self.debug else False
            for y, row in enumerate(self.hex_grid.grid):
                for x, _ in enumerate(row):
                    self.num_tiles += 1  # count the number of tiles when we're here anyway.
                    _hex: "Hex" = self.hex_grid.grid[x][y]
                    if _hex.is_land:
                        if _hex.distance <= 5:
                            _hex.moisture += 1
                        if _hex.distance <= 3:
                            _hex.moisture += random.randint(1, 3)
                        if _hex.distance <= 1:
                            _hex.moisture += random.randint(1, 6)

        # generate aquifers
        factor_min_max: int = 2
        max_aquifers: int = self.num_tiles // 80  # Floor Devide needs to be smaller to get the bigger integer
        min_aquifers: int = max_aquifers // factor_min_max
        num_aquifers = random.randint(min_aquifers, max_aquifers)

        if self.params.get("hydrosphere") is False or self.params.get("sea_percent") == 100:
            num_aquifers = 0

        aquifers: List["Hex"] = []
        while len(aquifers) < num_aquifers:
            rx = random.randint(0, len(self.hex_grid.grid) - 1)
            ry = random.randint(0, len(self.hex_grid.grid) - 1)
            _hex: "Hex" = self.hex_grid.grid[rx][ry]
            if _hex.is_land and _hex.moisture < 5:
                aquifers.append(_hex)

        for hex in aquifers:
            # print("Aquifer at ", hex)
            r1: List["Hex"] = hex.bubble(distance=3)
            for hex in r1:
                if hex.is_land:
                    hex.moisture += random.randint(0, 2)
            r2: List["Hex"] = hex.bubble(distance=2)
            for hex in r2:
                if hex.is_land:
                    hex.moisture += 1
            r3: List["Hex"] = hex.surrounding
            for hex in r3:
                if hex.is_land:
                    hex.moisture += 1

        if self.params.get("craters") is True:
            self.generate_craters()

        # volcanoes
        if self.params.get("volcanoes", True):
            self.generate_volcanoes()

        self.territories: List[Territory] = []

        self.generate_territories()

        self.geoforms: List[Geoform] = []

        self._determine_landforms()

        self._detect_lakes()

    def generate_craters(self):
        # decide number of craters
        num_craters = random.randint(0, 15)
        if self.debug:
            print("Making {} craters".format(num_craters))
        craters: List[Any] = []

        while len(craters) < num_craters:
            size = random.randint(1, 3)
            craters.append(
                dict(
                    hex=random.choice(self.hex_grid.hexes),
                    size=size,
                    depth=10 * size,
                )
            )

        for crater in craters:
            center_hex = crater.get("hex")
            size = crater.get("size")
            hexes: List["Hex"] = []

            if size >= 1:
                for hex in center_hex.surrounding:
                    hex.add_feature(HexFeature.crater)
                    hex.altitude = center_hex.altitude - 5
                    hex.altitude = max(hex.altitude, np.float64(0))
            elif size >= 2:
                hexes = center_hex.bubble(distance=2)
                for hex in hexes:
                    hex.add_feature(HexFeature.crater)
                    hex.altitude = center_hex.altitude - 10
                    hex.altitude = max(hex.altitude, np.float64(0))
            elif size >= 3:
                hexes = center_hex.bubble(distance=3)
                for hex in hexes:
                    hex.add_feature(HexFeature.crater)
                    hex.altitude = center_hex.altitude - 15
                    hex.altitude = max(hex.altitude, np.float64(0))

            for hex in hexes[: round(len(hexes) / 3)]:
                for i in hex.surrounding:
                    if i.has_feature(HexFeature.crater) is False:
                        i.add_feature(HexFeature.crater)
                        i.altitude = center_hex.altitude - 20
                        i.altitude = max(i.altitude, np.float64(0))

    def generate_volcanoes(self):
        num_volcanoes: int = int(self.params.get("num_volcanoes", 1))
        if self.debug:
            print("Making {} volcanoes".format(num_volcanoes))
        volcanoes: List[Dict[str, Any]] = []
        size: int = int(self.params.get("volcano_area_size", 1))
        while len(volcanoes) < num_volcanoes:
            center_hex: Hex = random.choice(self.hex_grid.hexes)
            neigh_tiles: List[Hex] | Hex = center_hex.bubble(distance=5)
            if neigh_tiles:
                for nh in neigh_tiles:
                    if nh.has_feature(HexFeature.volcano) or nh.is_water:
                        continue
            if center_hex.altitude < 50:
                continue
            extra_height = random.randint(75, 150)
            volcanoes.append(dict(hex=center_hex, size=size, height=extra_height))

        if size == 0 or size == 1:
            for volcano in volcanoes:
                height: int = volcano.get("height", 0)
                hex: "Hex" = volcano["hex"]
                if self.debug:
                    print(f"Volcano: Size: {size}, Height: {height}")
                hex.altitude = np.float64(
                    min(hex.altitude + height, self.params.get("height_range", (0, 255))[1] - 120)
                )
                hex.add_feature(HexFeature.volcano)

    def generate_territories(self):
        """
        Makes territories
        """
        # select number of territories to place
        num_territories = self.params.get("num_territories", 0)

        if self.debug:
            print("Making {} territories".format(num_territories)) if self.debug else False

        c = 0
        if num_territories == 0:
            return
        while len(self.territories) < num_territories:
            rx = random.randint(0, len(self.hex_grid.grid) - 1)
            ry = random.randint(0, len(self.hex_grid.grid) - 1)
            hex_s = self.hex_grid.grid[rx][ry]
            if hex_s.is_land:
                color = (
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255),
                )
                self.territories.append(Territory(self.hex_grid, hex_s, c, color))
                c += 1

        # loop over each, adding hexes
        total_hexes = self.hex_grid.size * self.hex_grid.size
        count = 0
        while count < total_hexes:  #  i in range(0, 15):
            count = 0
            territories = self.territories
            random.shuffle(territories)
            for t in territories:
                frontier = t.frontier
                for f in frontier:
                    if f.is_owned is False:
                        f.territory = t
                        t.members.append(f)
                        t.last_added.append(f)
                count += t.size

        # remove water hexes
        for t in self.territories:
            members = t.members
            t.members = [h for h in t.members if h.is_land]
            water_hexes = (h for h in members if h.is_water)
            for h in water_hexes:
                h.territory = None

        if self.debug:
            print("Merging barren territories")

        if self.params.get("num_territories", 0) > 0:
            top: List["Territory"] = []
            bottom: List["Territory"] = []
            for t in self.territories:
                avg_x = round(sum([i.x for i in t.members]) / len(t.members))
                if t.avg_temp() < 0 and (avg_x / self.hex_grid.size) < 0.5:
                    top.append(t)
                elif t.avg_temp() < 0 and (avg_x / self.hex_grid.size) >= 0.5:
                    bottom.append(t)

            pick_top = None
            pick_bottom = None
            if len(top) > 0:
                if self.debug:
                    print("Merging {} territories from the top of the map".format(len(top)))
                pick_top = random.choice(top)
                top.remove(pick_top)
                for t in self.territories:
                    if t in top:
                        pick_top.members += t.members
                        t.members = []

            if len(bottom) > 0:
                if self.debug:
                    print("Merging {} territories from the bottom of the map".format(len(bottom)))
                pick_bottom = random.choice(bottom)
                bottom.remove(pick_bottom)
                for t in self.territories:
                    if t in bottom:
                        pick_bottom.members += t.members
                        t.members = []

            if len(top) > 0 and pick_top is not None:
                for h in pick_top.members:
                    h.territory = pick_top

            if len(bottom) > 0 and pick_bottom is not None:
                for h in pick_bottom.members:
                    h.territory = pick_bottom

            self.territories = [t for t in self.territories]

            if self.debug:
                print(
                    "{} empty territories being deleted".format(
                        len([t for t in self.territories if len(t.members) == 0])
                    )
                )
            self.territories = [t for t in self.territories if len(t.members) > 0]

            if self.debug:
                print("There are now {} territories".format(len(self.territories)))

        if self.debug:
            print("Splitting territories into contiguous blocks") if self.debug else False
        for t in self.territories:
            t.find_groups()

    def _get_distances(self):
        """
        Gets the distances each land pixel is to the coastline.
        TODO: Make this more efficient
        """

        if not self.params.get("hydrosphere"):
            # we don't care about distances otherwise
            return

        for y, row in enumerate(self.hex_grid.grid):
            for x, _ in enumerate(row):
                h = self.hex_grid.grid[x][y]
                if h.is_land:
                    count = 1
                    numbers: List[int] = []

                    east = h.hex_east
                    while east.is_land is True and count < self.hex_grid.size * 2:
                        east = east.hex_east
                        count += 1
                    numbers.append(count)
                    count = 1

                    west = h.hex_west
                    while west.is_land is True and count < self.hex_grid.size * 2:
                        west = west.hex_west
                        count += 1
                    numbers.append(count)
                    count = 1

                    north_east = h.hex_north_east
                    while north_east.is_land is True and count < self.hex_grid.size * 2:
                        north_east = north_east.hex_north_east
                        count += 1
                    numbers.append(count)
                    count = 1

                    north_west = h.hex_north_west
                    while north_west.is_land is True and count < self.hex_grid.size * 2:
                        north_west = north_west.hex_north_west
                        count += 1

                    numbers.append(count)
                    count = 1

                    south_west = h.hex_south_west
                    while south_west.is_land is True and count < self.hex_grid.size * 2:
                        south_west = south_west.hex_south_west
                        count += 1
                    numbers.append(count)
                    count = 1

                    south_east = h.hex_south_east
                    while south_east.is_land is True and count < self.hex_grid.size * 2:
                        south_east = south_east.hex_south_east
                        count += 1
                    numbers.append(count)

                    h.distance = min(numbers)

    def _generate_rivers(self) -> None:
        """
        Generate rivers so they always end in sea or lake, or connect to each other:
        - pick N random high-altitude inland sources
        - follow the steepest downslope at each step
        - if next tile is sea (h.is_sea) or lake (h.is_lake), mark & stop
        - if another river ends within 2 tiles, connect to that river
        - if you get stuck on a plateau, spawn a lake there
        """
        num_rivers = self.params.get("num_rivers", 0)
        if self.debug:
            print(f"Making {num_rivers} rivers")

        # 1) pick all valid sources once
        candidates = [
            h for row in self.hex_grid.grid for h in row if h.is_inland and h.altitude > self.hex_grid.sealevel + 35
        ]
        if not candidates:
            if self.debug:
                print("No valid river sources found.")
            return

        sources = random.sample(candidates, min(num_rivers, len(candidates)))
        self.rivers_sources = [
            RiverSegment(self.hex_grid, h.x, h.y, random.choice(list(HexSide)), True) for h in sources
        ]

        # 2) grow each river
        self.rivers.clear()
        for src in self.rivers_sources:
            seg = src
            while True:
                down = seg.edge.down

                # ------------- river connection step -------------
                nearby = self._find_nearby_river_end(down, radius=2)
                if nearby:
                    path = self.hex_grid.straight_line_path((down.x, down.y), (nearby.x, nearby.y))
                    for px, py in path[1:]:  # [1:] skips the current hex
                        h = self.hex_grid.get(px, py)
                        if not h:
                            break
                        prev_hex = seg.edge.down
                        side = prev_hex.get_side_to(h)  # type: ignore
                        if side is not None:
                            edge = prev_hex.get_edge(side)  # type: ignore
                            if edge is None:
                                break
                            edge.is_river = True
                            seg.next = RiverSegment(self.hex_grid, px, py, side, False)  # type: ignore
                            seg = seg.next
                    # Mark the final segment as river too
                    seg.edge.is_river = True
                    break  # Connected, so end river here

                # stop if we've hit sea or lake
                if getattr(down, "is_sea", False) or getattr(down, "is_lake", False):
                    seg.edge.is_river = True
                    break

                # plateau → spawn a lake and stop
                nbrs = [(s, down.get_edge(s)) for s in HexSide]
                nbrs = [(s, e) for s, e in nbrs if e and e.down.altitude < down.altitude]
                if not nbrs:
                    down.add_feature(HexFeature.lake)
                    seg.edge.is_river = True
                    break

                # pick steepest next edge
                next_side, next_edge = min(nbrs, key=lambda se: se[1].down.altitude)

                # if next hex is water (but not necessarily lake) treat as sea end
                nxt = next_edge.down
                if getattr(nxt, "is_sea", False) or getattr(nxt, "is_lake", False):
                    next_edge.is_river = True
                    break

                # otherwise advance
                seg.next = RiverSegment(self.hex_grid, next_edge.one.x, next_edge.one.y, next_side, False)
                seg = seg.next

            # collect & mark whole chain
            s2 = src
            while s2:
                s2.edge.is_river = True
                self.rivers.append(s2)
                s2 = s2.next

    def _find_nearby_river_end(self, hex: "Hex", radius: int = 2):
        """
        Find a river segment in self.rivers that is an END (no .next)
        and is within 'radius' tiles of hex h. Returns the hex to connect to, or None.
        """
        for other in self.rivers:
            if other.next is not None:
                continue
            dist = self.hex_distance((hex.x, hex.y), (other.edge.down.x, other.edge.down.y))
            if 0 < dist <= radius:
                return other.edge.down
        return None

    def _detect_lakes(self) -> None:
        """
        Detects all lakes by finding clusters of connected water tiles
        that are fully surrounded by land (not connected to the map edge).
        Marks those clusters with HexFeature.lake.
        """
        from system.subsystems.hexgen.hex import Hex
        from gameplay.repositories.tile import TileRepository

        visited: Set[Hex] = set()
        size_x = len(self.hex_grid.grid)
        size_y = len(self.hex_grid.grid[0]) if size_x > 0 else 0

        # Helper to determine if a cluster touches the map edge
        def touches_edge(hexes: Set[Hex]) -> bool:
            for h in hexes:
                if h.x == 0 or h.y == 0 or h.x == size_x - 1 or h.y == size_y - 1:
                    return True
            return False

        # Scan all tiles in the map
        for x in range(size_x):
            for y in range(size_y):
                hex = self.hex_grid.grid[x][y]
                # Only process unvisited water tiles
                if hex in visited or not hex.is_water:
                    continue

                grid_dict = {
                    (x, y): self.hex_grid.grid[x][y]
                    for x in range(len(self.hex_grid.grid))
                    for y in range(len(self.hex_grid.grid[0]))
                }
                lakes, visited = TileRepository.flood_fill(hex, grid_dict, lambda t: t.is_water, visited)

                if not lakes:
                    continue

                # Only mark as a lake if not touching the map edge
                if not touches_edge(lakes):
                    for hex in lakes:
                        hex.add_feature(HexFeature.lake)
                    if self.debug:
                        print(f"Lake detected at {[(hex.x, hex.y) for hex in lakes]} (size: {len(lakes)})")
                # else: it's part of sea/ocean

        if self.debug:
            print("Lake detection complete.")

    def _determine_landforms(self):
        with Timer("Finding geographic features", self.debug):
            with Timer("\tPlacing initial geoforms", self.debug):
                for y, row in enumerate(self.hex_grid.grid):
                    for x, _ in enumerate(row):
                        h: Hex = self.hex_grid.grid[x][y]
                        if is_isthmus(h):
                            h.geoform_type = GeoformType.isthmus
                        elif is_bay(h):
                            h.geoform_type = GeoformType.bay
                        elif is_strait(h):
                            h.geoform_type = GeoformType.strait
                        elif is_peninsula(h):
                            h.geoform_type = GeoformType.peninsula
                        if h.geoform_type is not None:
                            self.geoforms.append(Geoform(set([h]), h.geoform_type))

            def flood_fill(start_hex: "Hex", target_type: Any) -> Set["Hex"]:
                queue = [start_hex]
                visited: Set["Hex"] = set()
                while queue:
                    current = queue.pop()
                    if current in visited or current.geoform_type is not None or current.type != target_type:
                        continue
                    visited.add(current)
                    queue.extend(n[1] for n in current.neighbors if n[1] not in visited)
                return visited

            def assign_geoform(hexes: Set["Hex"], geoform_type: GeoformType) -> None:
                for h in hexes:
                    h.geoform_type = geoform_type
                self.geoforms.append(Geoform(hexes, geoform_type))

            with Timer("\tFinding contiguous geoforms", self.debug):
                sys.setrecursionlimit(10000)
                current = first_hex_without_geoform(self.hex_grid.grid.tolist())
                while current is not None:
                    if current.is_land:
                        hexes = flood_fill(current, current.type)
                        size = len(hexes)
                        geotype = (
                            GeoformType.small_island
                            if size < 25
                            else GeoformType.large_island
                            if size < 100
                            else GeoformType.continent
                        )
                    else:
                        hexes = flood_fill(current, current.type)
                        size = len(hexes)
                        geotype = GeoformType.lake if size < 3 else GeoformType.sea if size < 100 else GeoformType.ocean
                    assign_geoform(hexes, geotype)
                    current = first_hex_without_geoform(self.hex_grid.grid.tolist())

            def calculate_neighbors():
                for geoform in self.geoforms:
                    geoform.neighbors.clear()
                for geoform in self.geoforms:
                    for h in geoform.hexes:
                        for _, n in h.neighbors:
                            ng = n.geoform
                            if ng and ng is not geoform:
                                geoform.neighbors.add(ng)
                for geoform in self.geoforms:
                    assert geoform not in geoform.neighbors

            with Timer("\tMerging geoforms", self.debug):
                calculate_neighbors()

                merged: Set[Geoform] = set()
                for geoform in list(self.geoforms):
                    for neighbor in list(geoform.neighbors):
                        if neighbor in merged or geoform in merged:
                            continue
                        if geoform.type == neighbor.type:
                            if self.debug:
                                print(f"Merging {geoform.type}")
                            geoform.merge(neighbor)
                            merged.add(neighbor)
                calculate_neighbors()

                for geoform in self.geoforms:
                    if geoform.type == GeoformType.isthmus:
                        islands = geoform.neighbor_of_type(GeoformType.small_island)
                        land_forms: List[Geoform] = geoform.neighbor_of_types(
                            [GeoformType.continent, GeoformType.small_island, GeoformType.large_island]
                        )
                        if len(islands) == 1 and len(land_forms) == 1:
                            island = islands[0]
                            if len(island.neighbor_of_type(GeoformType.isthmus)) <= 1:
                                if self.debug:
                                    print("Merging island + isthmus into peninsula")
                                island.merge(geoform)
                                island.type = GeoformType.peninsula
                calculate_neighbors()

                for geoform in list(self.geoforms):
                    if geoform.type == GeoformType.small_island:
                        large_islands = geoform.neighbor_of_type(GeoformType.large_island)
                        if large_islands:
                            if self.debug:
                                print("Merging small island into large island")
                            large_islands[0].merge(geoform)
                calculate_neighbors()

                for geoform in list(self.geoforms):
                    if geoform.type in (GeoformType.small_island, GeoformType.large_island):
                        isthmuses = geoform.neighbor_of_type(GeoformType.isthmus)
                        continents: set[Geoform] = set()
                        for i in isthmuses:
                            continents.update(i.neighbor_of_type(GeoformType.continent))
                        continents = set(continents)
                        continents_list = list(continents)
                        if len(continents_list) == 1:
                            if self.debug:
                                print("Merging island into continent")
                            continents_list[0].merge(geoform)
                        elif len(continents_list) > 1:
                            if self.debug:
                                print("Merging island and other continents into one continent")
                            continents_list[0].merge(geoform)
                            for c in continents_list[1:]:
                                continents_list[0].merge(c)
                calculate_neighbors()

                for geoform in list(self.geoforms):
                    if geoform.type == GeoformType.peninsula:
                        isthmuses = geoform.neighbor_of_type(GeoformType.isthmus)
                        if len(isthmuses) == 1:
                            if self.debug:
                                print("Merging isthmus into peninsula")
                            geoform.merge(isthmuses[0])
                        if geoform.size == 2 and len(geoform.neighbors) == 0:
                            geoform.type = GeoformType.small_island
                calculate_neighbors()

            if self.debug:
                print("Deleting {} geoforms".format(len([g for g in self.geoforms if g.to_delete is True])))
            self.geoforms = [g for g in self.geoforms if not g.to_delete]
            if self.debug:
                print("There is now {} geoforms".format(len(self.geoforms)))

    def is_river(self, edge: HexSide) -> bool:
        """
        Determines if an edge has a river
        :param edge: Edge
        :return: Boolean
        """
        for r in self.rivers_sources:
            while r.next is not None:
                if r.edge == edge:
                    return True
                r = r.next
        return False

    def hex_distance(self, a: tuple[int, int], b: tuple[int, int]) -> int:
        """
        Returns the distance (number of steps) between two hexes in axial coordinates (q, r).
        """
        aq, ar = a
        bq, br = b
        return (abs(aq - bq) + abs(aq + ar - bq - br) + abs(ar - br)) // 2

    def get_side_to(self, target_hex: "Hex") -> "HexSide | None":
        """
        Returns the HexSide direction from this hex to target_hex.
        Assumes self.neighbors is a dict {HexSide: Hex}.
        """
        for side, neighbor in self.neighbors.items():  # type: ignore
            if neighbor is target_hex:
                return side  # type: ignore
        return None

    def get_edge(self, side: "HexSide") -> "HexSide | None":
        """
        Returns the edge object for the given side.
        """
        return self.edges[side]  # type: ignore # Or however you store your edge objects

    @staticmethod
    def _axial_to_cube(q: int, r: int) -> Tuple[float, float, float]:
        """Convert axial (q, r) to cube (x, y, z) coords."""
        x = float(q)
        z = float(r)
        y = -x - z
        return x, y, z

    @staticmethod
    def _cube_to_axial(x: int, y: int, z: int) -> Tuple[int, int]:
        """Convert cube (x, y, z) back to axial (q, r)."""
        return x, z

    @staticmethod
    def _cube_lerp(a: float, b: float, t: float) -> float:
        """Linear interpolation between a and b."""
        return a + (b - a) * t

    @staticmethod
    def _cube_round(x: float, y: float, z: float) -> Tuple[int, int, int]:
        """Round floating cube coords to the nearest hex cube coords."""
        rx = round(x)
        ry = round(y)
        rz = round(z)

        x_diff = abs(rx - x)
        y_diff = abs(ry - y)
        z_diff = abs(rz - z)

        # fix the largest difference to ensure x + y + z = 0
        if x_diff > y_diff and x_diff > z_diff:
            rx = -ry - rz
        elif y_diff > z_diff:
            ry = -rx - rz
        else:
            rz = -rx - ry

        return rx, ry, rz

    def straight_line_path(self, a: Tuple[int, int], b: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Returns a list of axial coordinates (q, r) forming a straight-line path
        between hex a and hex b (inclusive) using cube-coordinate interpolation.
        """
        # Convert endpoints to cube coords
        x1, y1, z1 = self._axial_to_cube(*a)
        x2, y2, z2 = self._axial_to_cube(*b)

        # Number of steps
        N = self.hex_distance(a, b)
        path: List[Tuple[int, int]] = []

        for i in range(N + 1):
            t = 0.0 if N == 0 else i / N
            # interpolate each cube axis
            xi = self._cube_lerp(x1, x2, t)
            yi = self._cube_lerp(y1, y2, t)
            zi = self._cube_lerp(z1, z2, t)
            # round to nearest hex
            rx, ry, rz = self._cube_round(xi, yi, zi)
            # convert back to axial and append
            path.append(self._cube_to_axial(rx, ry, rz))

        return path

    def find_river(self, x: int, y: int) -> List[HexSide]:
        """Finds river segments at an hex's x and y coordinates. Returns a list of EdgeSides
        representing where the river segments are"""
        seg: List[HexSide] = []
        for s in self.rivers:
            if s.x == x and s.y == y:
                seg.append(s.side)
        return seg

    def debug_draw_hex_rivers(self) -> None:
        """
        Hex-based debug: gray=land, cyan=sea, dark blue=lakes, bright blue=rivers.
        """
        grid = self.hex_grid.grid
        cols, rows = len(grid), len(grid[0])
        fig, ax = plt.subplots(figsize=(16, 16))  # type: ignore

        # flat-topped hex parameters
        side: float = 1.0
        height: float = np.sqrt(3) * side

        # draw each hex
        for i in range(cols):
            for j in range(rows):
                h = grid[i][j]
                x = side * 1.5 * i
                y = height * (j + 0.5 * (i % 2))

                if h.has_feature(HexFeature.lake):
                    face = "#013f86"  # dark blue
                elif getattr(h, "is_water", False):
                    face = "#15b2d3"  # cyan
                else:
                    face = "#cccccc"  # light gray

                hex_patch = RegularPolygon(
                    (x, y),
                    numVertices=6,
                    radius=side,
                    orientation=np.pi / 6,  # flat top
                    facecolor=face,
                    edgecolor="k",
                    linewidth=0.2,
                )
                ax.add_patch(hex_patch)

        # overlay river points
        xs, ys = [], []
        for seg in self.rivers:
            xs.append(side * 1.5 * seg.x)  # type: ignore
            ys.append(height * (seg.y + 0.5 * (seg.x % 2)))  # type: ignore
        ax.scatter(xs, ys, c="b", s=10)  # type: ignore

        ax.set_aspect("equal")
        ax.axis("off")
        plt.savefig(f"debugging/river_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")  # type: ignore
