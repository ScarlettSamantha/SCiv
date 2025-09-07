import random
import sys
from itertools import count
from typing import Any, Callable, Deque, Dict, List, Set, Tuple

import numpy as np
from helpers.debug import Debug as DebugHelper
from system.subsystems.hexgen.enums import (
    GeoformType,
    HexFeature,
    MapType,
    OceanType,
)
from system.subsystems.hexgen.geoform import Geoform
from system.subsystems.hexgen.grid import Grid
from system.subsystems.hexgen.heightmap import Heightmap
from system.subsystems.hexgen.hex import Hex, HexSide
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
    "pressure": 1,
    "axial_tilt": 23,
    "craters": False,
    "volcanoes": True,
    "num_volcanoes": 5,
    "volcano_area_size": 1,
    "num_rivers": 50,
    "num_territories": 0,
    "desert_target_ratio": 0.12,
    "steppe_target_ratio": 0.10,
    "wind_dir": "west",
    "hadley_strength": 0.8,
    "coast_decay": 2.5,
    "rain_shadow_strength": 1.6,
    "lapse_rate_c_per_km": 6.5,
    "max_elev_m": 4000,
    "equator_temp": 28.0,
    "pole_temp": -20.0,
    "lake_to_sea_tiles": 100,
    "sea_to_ocean_tiles": 150,
}


class MapGen:
    def __init__(self, params: Dict[str, Any], debug: bool = False):
        self.params: Dict[str, Any] = {**default_params, **params}

        self.debug = bool(debug) or DebugHelper.world_generation()

        self._seed_rngs()

        with Timer("Building Heightmap", self.debug):
            self.heightmap = Heightmap(self.params, self.debug)

        self.hex_grid: Grid = Grid(self.heightmap, self.params)
        if self.debug:
            print("\tAverage Height: {}".format(self.hex_grid.average_height))
            print("\tHighest Height: {}".format(self.hex_grid.highest_height))
            print("\tLowest Height: {}".format(self.hex_grid.lowest_height))

        self.num_tiles: int = self.hex_grid.size * self.hex_grid.size

        self.rivers: List[Any] = []
        self.rivers_sources: List[RiverSegment] = []

        with Timer("Computing hex distances", self.debug):
            self._get_distances()

        if self.params.get("hydrosphere"):
            self._generate_rivers()

        factor_min_max: int = 2
        max_aquifers: int = self.num_tiles // 80
        min_aquifers: int = max_aquifers // factor_min_max
        num_aquifers = self.rng.randint(min_aquifers, max_aquifers) if max_aquifers > 0 else 0

        if not self.params.get("hydrosphere") or int(self.params.get("sea_percent", 0)) == 100:
            num_aquifers = 0

        aquifers: List["Hex"] = []
        while len(aquifers) < num_aquifers:
            rx = self.rng.randint(0, len(self.hex_grid.grid) - 1)
            ry = self.rng.randint(0, len(self.hex_grid.grid) - 1)
            _hex: "Hex" = self.hex_grid.grid[rx][ry]
            if _hex.is_land and _hex.moisture < 5:
                aquifers.append(_hex)

        for hex in aquifers:
            r1: List["Hex"] = hex.bubble(distance=3)
            for h in r1:
                if h.is_land:
                    h.moisture += self.rng.randint(0, 2)
            r2: List["Hex"] = hex.bubble(distance=2)
            for h in r2:
                if h.is_land:
                    h.moisture += 1
            r3: List["Hex"] = hex.surrounding
            for h in r3:
                if h.is_land:
                    h.moisture += 1

        if self.params.get("craters") is True:
            self.generate_craters()

        if self.params.get("volcanoes", True):
            self.generate_volcanoes()

        self.territories: List[Territory] = []
        self.geoforms: List[Geoform] = []

        self.generate_territories()

        self._determine_landforms()
        self._detect_lakes()

        if self.params.get("hydrosphere"):
            with Timer("Applying moisture diffusion (coast/rivers/lakes)", self.debug):
                self._apply_moisture()

        self._integrity_checks()

    def _apply_moisture(self) -> None:
        import math

        BIG = 10**9
        lam = float(self.params.get("coast_decay", 3.0))
        lam = max(0.5, lam)  # avoid div-by-zero; small half-hex limit

        def is_sea_coast_hex(h: Hex) -> bool:
            if not h.is_land:
                return False
            for _, n in h.neighbors:
                if n.is_water and getattr(n, "geoform", None) is not None:
                    if n.geoform.type in (GeoformType.sea, GeoformType.ocean):  # type: ignore[attr-defined]
                        return True
            return False

        sea_dist = self._distance_field(is_sea_coast_hex)
        A_coast = 6.0
        max_d = int(min(100, math.ceil(4.0 * lam)))

        for h, d in sea_dist.items():
            if d >= BIG or d > max_d:
                continue
            h.moisture += A_coast * math.exp(-float(d) / lam)

        river_sources: List[Hex] = []
        for h in self.hex_grid.hexes:
            if not h.is_land:
                continue
            edges = getattr(h, "edges", None)
            if not edges:
                continue
            if any(e is not None and getattr(e, "is_river", False) for e in edges):
                river_sources.append(h)

        if river_sources:
            A_river = 3.0
            lam_r = max(0.5, 0.7 * lam)
            steps_r = int(min(60, math.ceil(3.0 * lam_r)))
            self._diffuse_from_sources(river_sources, A_river, lam_r, steps_r)

        lake_edge_sources: List[Hex] = []
        for h in self.hex_grid.hexes:
            if not h.is_land:
                continue
            if (n.is_water and n.geoform == GeoformType.lake for _, n in h.neighbors):
                lake_edge_sources.append(h)

        if lake_edge_sources:
            A_lake = 4.5
            lam_l = 4.5
            steps_l = 3
            self._diffuse_from_sources(lake_edge_sources, A_lake, lam_l, steps_l)

    def generate_craters(self):
        num_craters = self.rng.randint(0, 15)
        if self.debug:
            print("Making {} craters".format(num_craters))
        craters: List[Any] = []

        while len(craters) < num_craters:
            size = self.rng.randint(1, 3)
            craters.append(
                dict(
                    hex=self.rng.choice(self.hex_grid.hexes),
                    size=size,
                    depth=10 * size,
                )
            )

        for crater in craters:
            center_hex: "Hex" = crater.get("hex")
            size = crater.get("size")
            hexes: List["Hex"] = []

            if size >= 1:
                for h in center_hex.surrounding:
                    h.add_feature(HexFeature.crater)
                    h.altitude = center_hex.altitude - 5
                    h.altitude = max(h.altitude, np.float64(0))
            elif size >= 2:
                hexes = center_hex.bubble(distance=2)
                for h in hexes:
                    h.add_feature(HexFeature.crater)
                    h.altitude = center_hex.altitude - 10
                    h.altitude = max(h.altitude, np.float64(0))
            elif size >= 3:
                hexes = center_hex.bubble(distance=3)
                for h in hexes:
                    h.add_feature(HexFeature.crater)
                    h.altitude = center_hex.altitude - 15
                    h.altitude = max(h.altitude, np.float64(0))

            for h in hexes[: round(len(hexes) / 3)]:
                for i in h.surrounding:
                    if i.has_feature(HexFeature.crater) is False:
                        i.add_feature(HexFeature.crater)
                        i.altitude = center_hex.altitude - 20
                        i.altitude = max(i.altitude, np.float64(0))

    def _local_ruggedness(self, h: "Hex") -> float:
        diffs = [abs(float(h.altitude) - float(n.altitude)) for _, n in h.neighbors]
        return sum(diffs) / max(1, len(diffs))

    def generate_volcanoes(self):
        num_volcanoes: int = int(self.params.get("num_volcanoes", 1))
        if self.debug:
            print("Making {} volcanoes".format(num_volcanoes))
        volcanoes: List[Dict[str, Any]] = []
        size: int = int(self.params.get("volcano_area_size", 1))

        tries = 0
        while len(volcanoes) < num_volcanoes and tries < num_volcanoes * 20:
            tries += 1
            center_hex: Hex = self.rng.choice(self.hex_grid.hexes)
            if center_hex.is_water or float(center_hex.altitude) < 50:
                continue
            if any(nh.has_feature(HexFeature.volcano) or nh.is_water for nh in center_hex.bubble(distance=5) or []):
                continue
            if self._local_ruggedness(center_hex) < 8.0:
                continue
            extra_height = self.rng.randint(75, 150)
            volcanoes.append(dict(hex=center_hex, size=size, height=extra_height))

        if size in (0, 1):
            for volcano in volcanoes:
                height: int = volcano.get("height", 0)
                h: "Hex" = volcano["hex"]
                if self.debug:
                    print(f"Volcano: Size: {size}, Height: {height}")
                h.altitude = np.float64(min(h.altitude + height, self.params.get("height_range", (0, 255))[1] - 120))
                h.add_feature(HexFeature.volcano)

    def generate_territories(self):
        num_territories = int(self.params.get("num_territories", 0))

        if self.debug:
            print("Making {} territories".format(num_territories))

        if num_territories == 0:
            return

        c = 0
        while len(self.territories) < num_territories:
            rx = self.rng.randint(0, len(self.hex_grid.grid) - 1)
            ry = self.rng.randint(0, len(self.hex_grid.grid) - 1)
            hex_s = self.hex_grid.grid[rx][ry]
            if hex_s.is_land:
                color = (
                    self.rng.randint(0, 255),
                    self.rng.randint(0, 255),
                    self.rng.randint(0, 255),
                )
                self.territories.append(Territory(self.hex_grid, hex_s, c, color))
                c += 1

        total_hexes = self.hex_grid.size * self.hex_grid.size
        count = 0
        while count < total_hexes:
            count = 0
            territories: List[Territory] = self.territories[:]
            self.rng.shuffle(territories)
            for t in territories:
                frontier = t.frontier
                for f in frontier:
                    if f.is_owned is False:
                        f.territory = t
                        t.members.append(f)
                        t.last_added.append(f)
                count += t.size

        for t in self.territories:
            members: List["Hex"] = t.members
            t.members = [h for h in t.members if h.is_land]
            water_hexes = (h for h in members if h.is_water)
            for h in water_hexes:
                h.territory = None

        if self.debug:
            print("Merging barren territories")

        if len(self.territories) > 0:
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
                pick_top = self.rng.choice(top)
                top.remove(pick_top)
                for t in self.territories:
                    if t in top:
                        pick_top.members += t.members
                        t.members = []

            if len(bottom) > 0:
                if self.debug:
                    print("Merging {} territories from the bottom of the map".format(len(bottom)))
                pick_bottom = self.rng.choice(bottom)
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
            print("Splitting territories into contiguous blocks")
        for t in self.territories:
            t.find_groups()

    def _get_distances(self) -> None:
        if not self.params.get("hydrosphere"):
            return

        from collections import deque

        grid: np.ndarray[Any, Any] = self.hex_grid.grid

        if hasattr(grid, "shape"):
            cols = int(grid.shape[0])
            rows = int(grid.shape[1]) if cols else 0
        else:
            cols = len(grid)
            rows = len(grid[0]) if cols else 0

        if cols == 0 or rows == 0:
            return

        BIG = 10**9
        for x in range(cols):
            for y in range(rows):
                h = grid[x][y]
                h.distance = BIG

        q: Deque[Any] = deque()
        for x in range(cols):
            for y in range(rows):
                h = grid[x][y]
                if not h.is_land:
                    continue
                if any(n.is_water for _, n in h.neighbors):
                    h.distance = 0
                    q.append(h)

        while q:
            cur = q.popleft()
            cd = cur.distance
            for _, n in cur.neighbors:
                if n.is_land and n.distance > cd + 1:
                    n.distance = cd + 1
                    q.append(n)

    def _seed_rngs(self) -> None:
        seed = self.params.get("random_seed")

        self.rng = random.Random(seed) if seed is not None else random.Random()

        if isinstance(seed, int):
            try:
                import numpy as _np

                _np.random.seed(seed % 2**32)
            except Exception:
                pass
            random.seed(seed)
        else:
            pass

        try:
            import numpy as _np

            self.np_rng = _np.random.default_rng(seed) if seed is not None else _np.random.default_rng()
        except Exception:
            self.np_rng = None

    def _generate_rivers(self) -> None:
        num_rivers = int(self.params.get("num_rivers", 0))
        if num_rivers <= 0:
            self.rivers = []
            self.rivers_sources = []
            return

        if self.debug:
            print(f"Making {num_rivers} rivers (drainage-based)")

        filled_alt: Dict[Hex, float] = self._priority_flood_filled_alt()
        flow_dir: Dict[Hex, float] = self._compute_flow_dir(filled_alt)
        acc: Dict[Hex, float] = self._flow_accumulation(flow_dir)

        margin: float = max(10.0, (self.hex_grid.sealevel if hasattr(self.hex_grid, "sealevel") else 0) + 10.0)
        candidates: List[Hex] = [h for h in self.hex_grid.hexes if h.is_inland and float(h.altitude) > margin]
        candidates.sort(key=lambda h: (acc.get(h, 0.0), float(h.altitude)), reverse=True)
        sources: List[Hex] = candidates[: min(num_rivers, len(candidates))]

        self.rivers.clear()
        self.rivers_sources = []

        for src_hex in sources:
            dn = flow_dir.get(src_hex)
            if dn is None:
                continue
            first_side = src_hex.get_side_to(dn)  # type: ignore
            if first_side is None:
                continue

            head = RiverSegment(self.hex_grid, src_hex.x, src_hex.y, first_side, True)  # type: ignore
            self.rivers_sources.append(head)

            cur_hex = src_hex
            cur_seg = head
            visited_chain = {cur_hex}

            while True:
                dn = flow_dir.get(cur_hex)  # type: ignore
                if dn is None:
                    break

                side_to_dn = cur_hex.get_side_to(dn)  # type: ignore
                if side_to_dn is None:
                    break

                edge = cur_hex.get_edge(side_to_dn)  # type: ignore
                if edge is None:
                    break

                already_river = edge.is_river  # type: ignore

                edge.is_river = True
                cur_seg.side = side_to_dn  # type: ignore

                if already_river:
                    break

                if dn in visited_chain:
                    break
                visited_chain.add(dn)  # type: ignore

                nxt = RiverSegment(self.hex_grid, dn.x, dn.y, side_to_dn, False)  # type: ignore
                cur_seg.next = nxt
                cur_seg = nxt
                cur_hex = dn

            s = head
            while s:
                self.rivers.append(s)
                s = s.next

        for seg in self.rivers:
            h = self.hex_grid.get(seg.x, seg.y)
            if not h or not h.is_land:
                continue
            h.moisture += 2
            for _, nhex in h.neighbors:
                if nhex.is_land:
                    nhex.moisture += 1
                for _, n2 in nhex.neighbors:
                    if n2.is_land:
                        n2.moisture += 0.5

    def _find_nearby_river_end(self, hex: "Hex", radius: int = 2):
        for other in self.rivers:
            if other.next is not None:
                continue
            dist = self.hex_distance((hex.x, hex.y), (other.edge.down.x, other.edge.down.y))
            if 0 < dist <= radius:
                return other.edge.down
        return None

    def _compute_flow_dir(self, filled_alt: Dict[Any, Any]) -> Dict[Any, Any]:
        flow_dir: Dict[Any, Any] = {}
        for h in self.hex_grid.hexes:
            if h.is_water:
                flow_dir[h] = None
                continue
            best = None
            best_alt = float(filled_alt[h])
            for _, n in h.neighbors:
                fa = float(filled_alt.get(n, n.altitude))
                if fa < best_alt:
                    best_alt = fa
                    best = n
            flow_dir[h] = best
        return flow_dir

    def _flow_accumulation(self, flow_dir: Dict[Any, Any]) -> Dict["Hex", float]:
        ordered: List[Hex] = sorted(
            (h for h in self.hex_grid.hexes if not h.is_water),
            key=lambda h: float(h.altitude),
            reverse=True,
        )
        acc: Dict["Hex", float] = {h: 1.0 for h in ordered}
        for h in ordered:
            d = flow_dir[h]
            if d is not None:
                acc[d] = acc.get(d, 1.0) + acc[h]
        return acc

    def _priority_flood_filled_alt(self) -> Dict["Hex", float]:
        import heapq
        import itertools

        grid = self.hex_grid.grid
        if hasattr(grid, "shape"):
            cols = int(grid.shape[0])
            rows = int(grid.shape[1]) if cols else 0
        else:
            cols = len(grid)
            rows = len(grid[0]) if cols else 0
        if cols == 0 or rows == 0:
            return {}

        filled_alt: Dict["Hex", float] = {}
        in_queue: Set["Hex"] = set()
        pq: List[Tuple[float, int, "Hex"]] = []
        tie: count[int] = itertools.count()

        def push(h: "Hex", alt: float) -> None:
            if h in in_queue:
                return
            in_queue.add(h)
            heapq.heappush(pq, (float(alt), next(tie), h))

        for x in range(cols):
            for y in range(rows):
                h = grid[x][y]
                if h.is_water:
                    push(h, float(h.altitude))
                elif x == 0 or y == 0 or x == cols - 1 or y == rows - 1:
                    push(h, float(h.altitude))

        eps = 1e-3

        while pq:
            alt, _, h = heapq.heappop(pq)  # type: ignore
            h: "Hex"
            if h in filled_alt:
                continue
            filled_alt[h] = alt
            for _, n in h.neighbors:
                if n in filled_alt:
                    continue
                n_alt = float(n.altitude)
                push(n, max(n_alt, alt + eps))

        return filled_alt

    def _detect_lakes(self) -> None:
        from collections import deque

        grid: np.ndarray[Any, Any] = self.hex_grid.grid
        size_x = len(grid)
        size_y = len(grid[0]) if size_x else 0
        if size_x == 0:
            return

        visited: Set["Hex"] = set()
        lake_to_sea = int(self.params.get("lake_to_sea_tiles", 60))

        for x in range(size_x):
            for y in range(size_y):
                h0 = grid[x][y]
                if not h0.is_water or h0 in visited:
                    continue

                comp: Set[Any] = set()
                q: Deque[Any] = deque([h0])
                visited.add(h0)
                touch = False

                while q:
                    h = q.popleft()
                    comp.add(h)
                    if h.x == 0 or h.y == 0 or h.x == size_x - 1 or h.y == size_y - 1:
                        touch = True
                    for _, n in h.neighbors:
                        if n.is_water and n not in visited:
                            visited.add(n)
                            q.append(n)

                if not touch and len(comp) <= lake_to_sea:
                    for h in comp:
                        h.add_feature(HexFeature.lake)
                    if self.debug:
                        print(f"Lake detected: size={len(comp)}")

    def _determine_landforms(self):
        with Timer("Finding geographic features", self.debug):

            def flood_fill(start_hex: "Hex", target_type: Any) -> set["Hex"]:
                queue: list["Hex"] = [start_hex]
                visited: set["Hex"] = set()
                while queue:
                    current = queue.pop()
                    if current in visited or current.type != target_type:
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

                grid = self.hex_grid.grid
                if hasattr(grid, "shape"):
                    cols = int(grid.shape[0])
                    rows = int(grid.shape[1]) if cols else 0
                else:
                    cols = len(grid)
                    rows = len(grid[0]) if cols else 0

                lake_to_sea = int(self.params.get("lake_to_sea_tiles", 60))
                sea_to_ocean = int(self.params.get("sea_to_ocean_tiles", 100))

                grid_list = self.hex_grid.grid.tolist()
                current: "Hex | None" = first_hex_without_geoform(grid_list)
                while current is not None:
                    if current.is_land:
                        hexes: Set["Hex"] = flood_fill(current, current.type)
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
                        size: int = len(hexes)
                        touches_edge = any((h.x == 0 or h.y == 0 or h.x == cols - 1 or h.y == rows - 1) for h in hexes)
                        if not touches_edge:
                            geotype = GeoformType.lake if size <= lake_to_sea else GeoformType.sea
                        else:
                            geotype = GeoformType.sea if size < sea_to_ocean else GeoformType.ocean

                    assign_geoform(hexes, geotype)
                    current = first_hex_without_geoform(grid_list)

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

            with Timer("\tAnnotating overlays (straits/bays/isthmuses/peninsulas)", self.debug):
                for y, row in enumerate(self.hex_grid.grid):
                    for x, _ in enumerate(row):
                        h: Hex = self.hex_grid.grid[x][y]
                        if is_isthmus(h):
                            h.add_feature(HexFeature.isthmus)
                        elif is_bay(h):
                            h.add_feature(HexFeature.bay)
                        elif is_strait(h):
                            h.add_feature(HexFeature.strait)
                        elif is_peninsula(h):
                            h.add_feature(HexFeature.peninsula)

    def _integrity_checks(self) -> None:
        if not self.debug:
            return
        bad_pairs = 0
        for g in self.geoforms:
            if g.type != GeoformType.lake:
                continue
            for h in g.hexes:
                for _, n in h.neighbors:
                    ng = getattr(n, "geoform", None)
                    if n.is_water and ng and ng.type in (GeoformType.sea, GeoformType.ocean):
                        bad_pairs += 1
                        print("[WARN] Lake touches sea/ocean at", h.x, h.y, "→", n.x, n.y)
                        break
        if bad_pairs == 0 and self.debug:
            print("Integrity: no lake-to-sea adjacency detected.")

    def is_river(self, edge: HexSide) -> bool:
        for r in self.rivers_sources:
            while r.next is not None:
                if r.edge == edge:
                    return True
                r = r.next  # type: ignore[assignment]
        return False

    def hex_distance(self, a: Tuple[int, int], b: Tuple[int, int]) -> int:
        aq, ar = a
        bq, br = b
        return (abs(aq - bq) + abs(aq + ar - bq - br) + abs(ar - br)) // 2

    @staticmethod
    def _axial_to_cube(q: int, r: int) -> Tuple[float, float, float]:
        x = float(q)
        z = float(r)
        y = -x - z
        return x, y, z

    @staticmethod
    def _cube_to_axial(x: int, y: int, z: int) -> Tuple[int, int]:
        return x, z

    @staticmethod
    def _cube_lerp(a: float, b: float, t: float) -> float:
        return a + (b - a) * t

    @staticmethod
    def _cube_round(x: float, y: float, z: float) -> Tuple[int, int, int]:
        rx: int = round(x)
        ry: int = round(y)
        rz: int = round(z)

        x_diff: float = abs(rx - x)
        y_diff: float = abs(ry - y)
        z_diff: float = abs(rz - z)

        if x_diff > y_diff and x_diff > z_diff:
            rx = -ry - rz
        elif y_diff > z_diff:
            ry = -rx - rz
        else:
            rz = -rx - ry

        return rx, ry, rz

    def straight_line_path(self, a: Tuple[int, int], b: Tuple[int, int]) -> List[Tuple[int, int]]:
        x1, y1, z1 = self._axial_to_cube(*a)
        x2, y2, z2 = self._axial_to_cube(*b)

        N = self.hex_distance(a, b)
        path: List[Tuple[int, int]] = []

        for i in range(N + 1):
            t = 0.0 if N == 0 else i / N

            xi: float = self._cube_lerp(x1, x2, t)
            yi: float = self._cube_lerp(y1, y2, t)
            zi: float = self._cube_lerp(z1, z2, t)

            rx, ry, rz = self._cube_round(xi, yi, zi)

            path.append(self._cube_to_axial(rx, ry, rz))

        return path

    def find_river(self, x: int, y: int) -> List[HexSide]:
        seg: List[HexSide] = []
        for s in self.rivers:
            if s.x == x and s.y == y:
                seg.append(s.side)
        return seg

    def _distance_field(self, is_source_hex: Callable[[Hex], bool]) -> Dict[Hex, int]:
        from collections import deque

        dist: Dict[Hex, int] = {}
        q: Deque[Hex] = deque()

        for h in self.hex_grid.hexes:
            if h.is_land and is_source_hex(h):
                dist[h] = 0
                q.append(h)

        while q:
            cur = q.popleft()
            cd = dist[cur]
            for _, n in cur.neighbors:
                if not n.is_land:
                    continue
                if n not in dist:
                    dist[n] = cd + 1
                    q.append(n)

        return dist

    def _diffuse_from_sources(self, sources: List[Hex], amplitude: float, lam: float, max_steps: int) -> None:
        import math
        from collections import deque

        if not sources:
            return

        visited: Set[Hex] = set()
        q: Deque[Tuple[Hex, int]] = deque()

        for s in sources:
            if s.is_land and s not in visited:
                visited.add(s)
                q.append((s, 0))
                s.moisture += amplitude

        while q:
            cur, d = q.popleft()
            nd = d + 1
            if nd > max_steps:
                continue
            for _, n in cur.neighbors:
                if not n.is_land or n in visited:
                    continue
                visited.add(n)
                n.moisture += amplitude * math.exp(-float(nd) / lam)
                q.append((n, nd))
