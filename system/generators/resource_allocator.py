import random
from typing import Dict, List, Tuple, Type

from gameplay.resource import BaseResource, ResourceSpawnablePlace
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.tiles.base_tile import BaseTile


class ResourceAllocator:

    def __init__(self, grid: Dict[Tuple[int, int], BaseTile], resources: List[Type[BaseResource]]) -> None:
        self.grid: Dict[Tuple[int, int], BaseTile] = grid
        self.grid_width: int = max([t.x for t in grid.values()]) + 1
        self.grid_height: int = max([t.y for t in grid.values()]) + 1
        self.resources: List[Type[BaseResource]] = resources

    def allocate_resources(self) -> None:
        resource_class: Type[BaseResource]
        for resource_class in self.resources:
            coverage_percent: float = self._decide_coverage_for(resource_class)
            if coverage_percent <= 0:
                continue

            self._allocate_single_resource(resource_class, coverage_percent)

    def _decide_coverage_for(self, resource_class: Type[BaseResource]) -> float:
        if isinstance(resource_class.coverage, tuple):
            min_coverage, max_coverage = resource_class.coverage
            return random.uniform(min_coverage, max_coverage)
        elif isinstance(resource_class.coverage, (float, int)):
            return resource_class.coverage
        else:
            return 0.0

    def _allocate_single_resource(self, resource_class: Type[BaseResource], coverage_percent: float) -> None:
        # get valid candidate tiles for this resource
        candidate_tiles: List[BaseTile] = self._filter_valid_tiles(resource_class)

        # figure out how many of them we want to fill
        total_map_tiles: int = len(self.grid)
        desired_count: int = int((coverage_percent / 100.0) * total_map_tiles)
        if desired_count <= 0:
            return

        # randomly sample from the candidate tiles
        if resource_class.clusterable:
            self._allocate_with_clustering(resource_class, candidate_tiles, desired_count)
        else:
            self._allocate_without_clustering(resource_class, candidate_tiles, desired_count)

    def _filter_valid_tiles(self, resource_class: Type[BaseResource]) -> List[BaseTile]:
        valid_tiles: List[BaseTile] = []
        for tile in self.grid.values():
            if (
                tile.resource is not None and len(list(tile.resource.values())) > 0
            ):  # skip if there's already a resource
                continue

            if not self._terrain_allows_resource(tile, resource_class):  # skip if terrain doesn't allow
                continue

            # @TODO can add more checks here to determine if a tile is valid
            # if tile.extra_data.temp < -1.0 and resource_class is X: skip

            valid_tiles.append(tile)

        return valid_tiles

    def _terrain_allows_resource(self, tile: BaseTile, resource_class: Type[BaseResource]) -> bool:
        if tile.is_water and resource_class.spawn_type == ResourceSpawnablePlace.LAND:
            return False
        if not tile.is_water and resource_class.spawn_type == ResourceSpawnablePlace.WATER:
            return False

        if hasattr(resource_class, "on_world_place_tile_filter"):
            if resource_class.on_world_place_tile_filter(self, tile) is False:
                return False

        # if the tile's terrain is not in spawn_chance dict or is 0
        spawn_chance: float | Dict[Type[BaseTerrain], float] = resource_class.spawn_chance
        terrain_type: Type[BaseTerrain] = tile.get_terrain().__class__

        if isinstance(spawn_chance, dict):
            # look up
            chance_for_terrain: float = spawn_chance.get(terrain_type, spawn_chance.get(BaseTerrain, 0.0))
            return chance_for_terrain > 0.0
        else:
            # it's a flat float
            return spawn_chance > 0.0

    def _allocate_without_clustering(
        self, resource_class: Type[BaseResource], candidate_tiles: List[BaseTile], desired_count: int
    ) -> None:
        if not candidate_tiles:
            return

        # sample if we have more candidates than we need
        to_fill: List[BaseTile] = random.sample(candidate_tiles, min(desired_count, len(candidate_tiles)))

        tile: BaseTile
        for tile in to_fill:
            # final chance roll per tile:
            if self._roll_spawn_chance(tile, resource_class):
                self._assign_resource(tile, resource_class)

    def _roll_spawn_chance(self, tile: BaseTile, resource_class: Type[BaseResource]) -> bool:
        spawn_chance: float | Dict[Type[BaseTerrain], float] = resource_class.spawn_chance
        terrain_type = tile.get_terrain().__class__
        if isinstance(spawn_chance, dict):
            chance_for_terrain = spawn_chance.get(terrain_type, spawn_chance.get(BaseTerrain, 0.0))
            return random.uniform(0, 100) < chance_for_terrain
        else:
            return random.uniform(0, 100) < spawn_chance

    def _assign_resource(self, tile: BaseTile, resource_class: Type[BaseResource]) -> None:
        tile.add_resource(resource_class())  # Assign resource to tile

    def _allocate_with_clustering(
        self, resource_class: Type[BaseResource], candidate_tiles: List[BaseTile], desired_count: int
    ) -> None:
        count_placed = 0
        remaining_tiles = set(candidate_tiles)

        # shuffle to make sure we pick random cluster centers
        random.shuffle(candidate_tiles)

        for center_tile in candidate_tiles:
            if count_placed >= desired_count:
                break

            # final chance roll for the center tile:
            if not self._roll_spawn_chance(center_tile, resource_class):
                continue
            # place on center tile
            self._assign_resource(center_tile, resource_class)
            count_placed += 1
            remaining_tiles.discard(center_tile)

            # do BFS/“bubble” for neighbors
            cluster_size = self._spread_cluster(
                resource_class, center_tile, remaining_tiles, desired_count - count_placed
            )
            count_placed += cluster_size

    def get_neighbors(
        self, tile: "BaseTile", radius: int = 1, check_passable: bool = False, climbable: bool = False
    ) -> List["BaseTile"]:
        from collections import deque

        directions_even = [(+1, 0), (+1, -1), (0, -1), (-1, -1), (-1, 0), (0, +1)]
        directions_odd = [(+1, 0), (0, -1), (-1, 0), (-1, +1), (0, +1), (+1, +1)]

        visited = set([tile])
        result = []
        queue = deque([(tile, 0)])

        while queue:
            current_tile, dist = queue.popleft()
            # Include tiles that are within [1, radius] steps, but not the original tile
            if 0 < dist <= radius:
                result.append(current_tile)
            if dist < radius:
                # Determine neighbor directions based on odd/even x of current tile
                curr_directions = directions_even if current_tile.x % 2 == 0 else directions_odd
                for dx, dy in curr_directions:
                    nx, ny = current_tile.x + dx, current_tile.y + dy
                    if nx < 0 or ny < 0 or nx > self.grid_width - 1 or ny > self.grid_height - 1:  # Skip out-of-bounds
                        continue
                    neighbor = self.grid[(nx, ny)]
                    if neighbor and neighbor not in visited:
                        # Apply passable or climbable checks
                        if check_passable and not neighbor.is_passable():
                            continue
                        if climbable and not neighbor.get_climbable():
                            continue
                        visited.add(neighbor)
                        queue.append((neighbor, dist + 1))

        return result

    def _spread_cluster(
        self, resource_class: Type[BaseResource], center_tile: BaseTile, remaining_tiles: set, limit: int
    ) -> int:
        placed = 0
        if not resource_class.clusterable:
            return 0

        # figure out max radius
        if isinstance(resource_class.cluster_max_radius, int):
            max_radius = resource_class.cluster_max_radius
        else:
            max_radius = random.randint(*resource_class.cluster_max_radius)

        # figure out dropoff
        if isinstance(resource_class.cluster_dropoff_amount_rate, float):
            dropoff = resource_class.cluster_dropoff_amount_rate
        else:
            rate = resource_class.cluster_dropoff_amount_rate
            if isinstance(rate, tuple):
                dropoff = random.uniform(rate[0], rate[1])
            else:
                dropoff = float(rate)

        cluster_hexes = self.get_neighbors(center_tile, max_radius, check_passable=True)

        random.shuffle(cluster_hexes)  # shuffle them so we don’t just do rings in strict order

        h: BaseTile
        for h in cluster_hexes:
            if limit <= 0:
                break
            # skip the center tile (already done) or if it's not in remaining set
            if h == center_tile:
                continue
            if h not in remaining_tiles:
                continue

            # distance-based probability
            dist = self._hex_distance(center_tile, h)
            new_probability = (1.0 - (dropoff * dist)) * resource_class.clusterable
            if new_probability <= 0:
                continue

            # final random check
            if random.uniform(0, 1) <= new_probability:
                self._assign_resource(h, resource_class)
                placed += 1
                limit -= 1
                remaining_tiles.discard(h)

        return placed

    def _hex_distance(self, tile_1: BaseTile, tile_2: BaseTile) -> int:
        dx = abs(tile_1.x - tile_2.x)
        dy = abs(tile_1.y - tile_2.y)
        return max(dx, dy, abs(dx - dy))
