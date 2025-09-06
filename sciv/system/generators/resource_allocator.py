import random
from typing import TYPE_CHECKING, Dict, List, Set, Tuple, Type

from gameplay.resource import BaseResource, ResourceSpawnablePlace
from gameplay.terrain._base_terrain import BaseTerrain

if TYPE_CHECKING:
    from gameplay.tile import Tile


class ResourceAllocator:
    def __init__(self, grid: Dict[Tuple[int, int], "Tile"], resources: List[Type[BaseResource]]) -> None:
        self.grid: Dict[Tuple[int, int], "Tile"] = grid
        self.grid_width: int = max([t.x for t in grid.values()]) + 1
        self.grid_height: int = max([t.y for t in grid.values()]) + 1
        self.resources: List[Type[BaseResource]] = resources

    def allocate_resources(self) -> None:
        for resource_class in self.resources:
            coverage_percent: float = self._decide_coverage_for(resource_class)
            if coverage_percent <= 0:
                continue
            self._allocate_single_resource(resource_class, coverage_percent)

    def _decide_coverage_for(self, resource_class: Type[BaseResource]) -> float:
        if isinstance(resource_class.coverage, tuple):
            min_coverage, max_coverage = resource_class.coverage
            return random.uniform(min_coverage, max_coverage)
        return float(resource_class.coverage)

    def _filter_valid_tiles(self, resource_class: Type[BaseResource]) -> List["Tile"]:
        valid_tiles: List["Tile"] = []
        for tile in self.grid.values():
            if tile.resources.has_non_mechanical_resources():
                continue
            if not self._terrain_allows_resource(tile, resource_class):
                continue
            valid_tiles.append(tile)
        return valid_tiles

    def _terrain_allows_resource(self, tile: "Tile", resource_class: Type[BaseResource]) -> bool:
        if tile.is_water and resource_class.spawn_type == ResourceSpawnablePlace.LAND:
            return False
        if not tile.is_water and resource_class.spawn_type == ResourceSpawnablePlace.WATER:
            return False
        if resource_class.on_world_place_tile_filter(self, tile) is False:
            return False
        spawn_chance: float | Dict[Type[BaseTerrain], float] = resource_class.spawn_chance
        terrain_type: Type[BaseTerrain] = tile.get_terrain().__class__
        if isinstance(spawn_chance, dict):
            chance_for_terrain: float = spawn_chance.get(terrain_type, spawn_chance.get(BaseTerrain, 0.0))
            return chance_for_terrain > 0.0
        else:
            return float(spawn_chance) > 0.0

    def _allocate_single_resource(self, resource_class: Type[BaseResource], coverage_percent: float) -> None:
        candidate_tiles: List["Tile"] = self._filter_valid_tiles(resource_class)
        if not candidate_tiles:
            return
        total_map_tiles: int = len(self.grid)
        desired_count: int = int((coverage_percent / 100.0) * total_map_tiles)
        if desired_count <= 0:
            return
        components: List[List["Tile"]] = self._connected_components(candidate_tiles)
        if len(components) == 1:
            tiles = components[0]
            if resource_class.clusterable:
                self._allocate_with_clustering(resource_class, tiles, desired_count)
            else:
                self._allocate_without_clustering(resource_class, tiles, desired_count)
            return
        sizes: List[int] = [len(c) for c in components]
        quotas: List[int] = self._distribute_quota(desired_count, sizes)
        order: List[int] = list(range(len(components)))
        random.shuffle(order)
        for idx in order:
            comp_tiles: List[Tile] = components[idx]
            comp_quota: int = quotas[idx]
            if comp_quota <= 0:
                continue
            if resource_class.clusterable:
                self._allocate_with_clustering(resource_class, comp_tiles, comp_quota)
            else:
                self._allocate_without_clustering(resource_class, comp_tiles, comp_quota)

    def _distribute_quota(self, target: int, sizes: List[int]) -> List[int]:
        total: int = sum(sizes)
        if total == 0 or target <= 0:
            return [0] * len(sizes)
        raw: List[float] = [(s / total) * target for s in sizes]
        base: List[int] = [int(x) for x in raw]
        remainder: int = target - sum(base)
        if remainder > 0:
            frac_idx: List[int] = sorted(range(len(sizes)), key=lambda i: (raw[i] - base[i]), reverse=True)
            for i in frac_idx[:remainder]:
                base[i] += 1
        return base

    def _allocate_without_clustering(
        self, resource_class: Type[BaseResource], candidate_tiles: List["Tile"], desired_count: int
    ) -> None:
        if not candidate_tiles or desired_count <= 0:
            return
        sample_size: int = min(desired_count, len(candidate_tiles))
        to_try: List["Tile"] = random.sample(candidate_tiles, sample_size)
        for tile in to_try:
            if tile.resources.has_non_mechanical_resources():
                continue
            if self._roll_spawn_chance(tile, resource_class):
                self._assign_resource(tile, resource_class)

    def _allocate_with_clustering(
        self, resource_class: Type[BaseResource], candidate_tiles: List["Tile"], desired_count: int
    ) -> None:
        if not candidate_tiles or desired_count <= 0:
            return
        count_placed = 0
        remaining_tiles: Set["Tile"] = set(candidate_tiles)
        centers: List["Tile"] = candidate_tiles[:]
        random.shuffle(centers)
        for center_tile in centers:
            if count_placed >= desired_count:
                break
            if center_tile not in remaining_tiles:
                continue
            if not self._roll_spawn_chance(center_tile, resource_class):
                remaining_tiles.discard(center_tile)
                continue
            self._assign_resource(center_tile, resource_class)
            count_placed += 1
            remaining_tiles.discard(center_tile)
            placed = self._spread_cluster(resource_class, center_tile, remaining_tiles, desired_count - count_placed)
            count_placed += placed

    def _roll_spawn_chance(self, tile: "Tile", resource_class: Type[BaseResource]) -> bool:
        spawn_chance: float | Dict[Type[BaseTerrain], float] = resource_class.spawn_chance
        terrain_type = tile.get_terrain().__class__
        if isinstance(spawn_chance, dict):
            chance_for_terrain = spawn_chance.get(terrain_type, spawn_chance.get(BaseTerrain, 0.0))
            return random.uniform(0.0, 100.0) < chance_for_terrain
        else:
            return random.uniform(0.0, 100.0) < float(spawn_chance)

    def _assign_resource(self, tile: "Tile", resource_class: Type[BaseResource]) -> None:
        resource = resource_class()
        resource.value = 1
        tile.add_resource(resource)

    def _spread_cluster(
        self, resource_class: Type[BaseResource], center_tile: "Tile", remaining_tiles: Set["Tile"], limit: int
    ) -> int:
        placed = 0
        if not resource_class.clusterable or limit <= 0:
            return 0
        if isinstance(resource_class.cluster_max_radius, int):
            max_radius = resource_class.cluster_max_radius
        else:
            max_radius = random.randint(*resource_class.cluster_max_radius)
        rate = resource_class.cluster_dropoff_amount_rate
        if isinstance(rate, tuple):
            dropoff = random.uniform(rate[0], rate[1])
        else:
            dropoff = float(rate)
        cluster_hexes = self.get_neighbors(center_tile, max_radius, check_passable=True)
        random.shuffle(cluster_hexes)
        for h in cluster_hexes:
            if limit <= 0:
                break
            if h is center_tile or h not in remaining_tiles:
                continue
            dist = self._hex_distance(center_tile, h)
            new_probability = (1.0 - (dropoff * dist)) * resource_class.clusterable
            if new_probability <= 0.0:
                continue
            if random.uniform(0.0, 1.0) <= new_probability:
                self._assign_resource(h, resource_class)
                placed += 1
                limit -= 1
                remaining_tiles.discard(h)
        return placed

    def get_neighbors(
        self, tile: "Tile", radius: int = 1, check_passable: bool = False, climbable: bool = False
    ) -> List["Tile"]:
        from collections import deque

        directions_even: List[Tuple[int, int]] = [(+1, 0), (+1, -1), (0, -1), (-1, -1), (-1, 0), (0, +1)]
        directions_odd: List[Tuple[int, int]] = [(+1, 0), (0, -1), (-1, 0), (-1, +1), (0, +1), (+1, +1)]
        visited: Set["Tile"] = {tile}
        result: List["Tile"] = []
        queue: deque[tuple["Tile", int]] = deque([(tile, 0)])
        while queue:
            current_tile, dist = queue.popleft()
            if 0 < dist <= radius:
                result.append(current_tile)
            if dist < radius:
                curr_directions: List[Tuple[int, int]] = directions_even if current_tile.x % 2 == 0 else directions_odd
                for dx, dy in curr_directions:
                    nx, ny = current_tile.x + dx, current_tile.y + dy
                    if nx < 0 or ny < 0 or nx >= self.grid_width or ny >= self.grid_height:
                        continue
                    neighbor: "Tile" = self.grid[(nx, ny)]
                    if neighbor not in visited:
                        if check_passable and not neighbor.is_passable():
                            continue
                        if climbable and not neighbor.get_climbable():
                            continue
                        visited.add(neighbor)
                        queue.append((neighbor, dist + 1))
        return result

    def _hex_distance(self, tile_1: "Tile", tile_2: "Tile") -> int:
        dx = abs(tile_1.x - tile_2.x)
        dy = abs(tile_1.y - tile_2.y)
        return max(dx, dy, abs(dx - dy))

    def _connected_components(self, candidate_tiles: List["Tile"]) -> List[List["Tile"]]:
        cand_set: Set["Tile"] = set(candidate_tiles)
        unvisited: Set["Tile"] = set(candidate_tiles)
        components: List[List["Tile"]] = []
        while unvisited:
            start: "Tile" = unvisited.pop()
            comp: List["Tile"] = [start]
            stack: List["Tile"] = [start]
            while stack:
                t: "Tile" = stack.pop()
                for nx, ny in self._neighbor_coords(t.x, t.y):
                    if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                        n: "Tile" = self.grid[(nx, ny)]
                        if n in cand_set and n in unvisited:
                            unvisited.remove(n)
                            comp.append(n)
                            stack.append(n)
            components.append(comp)
        return components

    def _neighbor_coords(self, x: int, y: int) -> List[Tuple[int, int]]:
        if x % 2 == 0:
            dirs: List[Tuple[int, int]] = [(+1, 0), (+1, -1), (0, -1), (-1, -1), (-1, 0), (0, +1)]
        else:
            dirs: List[Tuple[int, int]] = [(+1, 0), (0, -1), (-1, 0), (-1, +1), (0, +1), (+1, +1)]
        return [(x + dx, y + dy) for dx, dy in dirs]
