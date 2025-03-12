from heapq import heappop, heappush
from typing import Dict, List, Optional, Tuple

from gameplay.tiles.base_tile import BaseTile
from managers.world import World


class TileRepository:
    instance_ref_grid: World = World.get_instance()

    def __init__(self) -> None:
        pass

    @classmethod
    def get_tile(cls, x: int, y: int) -> Optional[BaseTile]:
        """
        Retrieve the tile at the given (x, y) coordinate from the world's grid.

        :param x: x-coordinate
        :param y: y-coordinate
        :return: The Tile at (x, y) if it exists; otherwise, None.
        """
        _tile = World.get_instance().grid.get((x, y))
        if _tile:
            return _tile
        return None

    @classmethod
    def get_tiles_in_radius(cls, tile: BaseTile, radius: int) -> List[BaseTile]:
        r"""
        Retrieves all tiles within a given hexagonal radius from the specified tile.

        The algorithm iterates over concentric "rings" around the origin tile.
        For each ring of radius 'r', it moves in the 6 hexagonal directions.

        Example (for radius 1):

        | = = = = = = = = = = = = = = = = = |
        |              _ _ _ _              |
        |             /       \             |
        |            /         \            |
        |    _ _ _ _/     T     \_ _ _ _    |
        |   /       \    1,0    /       \   |
        |  /         \         /         \  |
        | /     TL    \_ _ _ _/     TR    \ |
        | \    0,1    /       \    2,0    / |
        |  \         /         \         /  |
        |   \_ _ _ _/     C     \_ _ _ _/   |
        |   /       \    1,1    /       \   |
        |  /         \         /         \  |
        | /     BL    \_ _ _ _/     BR    \ |
        | \    0,2    /       \    2,1    / |
        |  \         /         \         /  |
        |   \_ _ _ _/     B     \_ _ _ _/   |
        |           \    1,2    /           |
        |            \         /            |
        |             \_ _ _ _/             |
        |                                   |
        | = = = = = = = = = = = = = = = = = |
        Each edge of the hexagon is traversed to collect the neighbors.

        :param tile: The origin tile.
        :param radius: The radius (in hex steps) to search.
        :return: List of Tile objects within the specified radius.
        """
        directions = [(+1, 0), (+1, -1), (0, -1), (-1, 0), (-1, +1), (0, +1)]
        tiles = []
        for r in range(1, radius + 1):
            for dx, dy in directions:
                x, y = tile.x, tile.y
                for _ in range(r):
                    x += dx
                    y += dy
                    _tile = cls.get_tile(x, y)
                    if _tile is not None:
                        tiles.append(_tile)
        return tiles

    @staticmethod
    def _offset_to_cube(x: int, y: int) -> Tuple[int, int, int]:
        r"""
        Converts offset coordinates (assuming an odd‑q layout) to cube coordinates.
        This conversion is helpful to calculate hex distances.

        In an odd‑q system:
          - x corresponds to the column (q)
          - y corresponds to the row (r)

        The conversion formulas are:
            cube_x = x
            cube_z = y - ((x - (x & 1)) // 2)
            cube_y = -cube_x - cube_z

        Cube Coordinate System Diagram:

                  z
                  |
                  |   / y
                  |  /
                  | /
            ------+------> x
                  |

        :param x: Offset x-coordinate.
        :param y: Offset y-coordinate.
        :return: Tuple of cube coordinates (cube_x, cube_y, cube_z).
        """
        cube_x = x
        cube_z = y - ((x - (x & 1)) // 2)
        cube_y = -cube_x - cube_z
        return cube_x, cube_y, cube_z

    @classmethod
    def heuristic(cls, tile_a: BaseTile, tile_b: BaseTile) -> float:
        r"""
        Computes the hex distance between two tiles by converting them to cube coordinates.

        Steps:
          1. Convert both tiles from offset to cube coordinates.
          2. Compute the maximum of the absolute differences along the cube axes.

        Cube Distance Formula:
            distance = max(|dx|, |dy|, |dz|)

        Diagram:

                z
                |
                |   / y
                |  /
                | /
          ------+------> x
                |

        :param tile_a: Starting tile.
        :param tile_b: Target tile.
        :return: The hex distance as a float.
        """
        ax, ay, az = cls._offset_to_cube(tile_a.x, tile_a.y)
        bx, by, bz = cls._offset_to_cube(tile_b.x, tile_b.y)
        return float(max(abs(ax - bx), abs(ay - by), abs(az - bz)))

    @classmethod
    def heuristic_tiles(cls, tile_a: "BaseTile", tile_b: "BaseTile") -> float:
        """
        Estimates the cost between two tiles based on their coordinates.

        This heuristic uses a Manhattan-like approach.

        :param tile_a: Starting tile.
        :param tile_b: Target tile.
        :return: Estimated cost as a float.
        """
        return abs(tile_a.x - tile_b.x) + abs(tile_a.y - tile_b.y)

    @classmethod
    def get_neighbors(
        cls, tile: "BaseTile", radius: int = 1, check_passable: bool = False, climbable: bool = False
    ) -> List["BaseTile"]:
        r"""
        Returns all tiles within the specified radius in an offset hex grid (q-odd layout) using cls.instance_ref_grid.grid.

        For a radius of 1, neighbors are the 6 adjacent tiles. For larger radii, any tile within that many steps is included.

        For even x-coordinates, the neighbor directions are:
            (+1, 0), (+1, -1), (0, -1), (-1, -1), (-1, 0), (0, +1)

        For odd x-coordinates, the directions are:
            (+1,  0), (0, -1), (-1,  0), (-1, +1), (0, +1), (+1, +1)

        ASCII representation (for even x):

                (-1,-1)   (0,-1)
                    \     /
                     \   /
                (-1,0) X (+1,0)
                     /   \
                    /     \
               (0,+1)   (+1,-1)

        The method optionally filters tiles based on whether they are passable or climbable.

        :param tile: The tile whose neighbors are to be fetched.
        :param radius: The maximum distance from the tile to be included. Default is 1.
        :param check_passable: If True, only include passable tiles.
        :param climbable: If True, only include tiles that are climbable.
        :return: List of neighboring Tile objects within the specified radius.
        :raises ValueError: If the global grid reference is not set.
        """
        from collections import deque

        if cls.instance_ref_grid is None:
            raise ValueError("instance_ref_grid must be set before calling get_neighbors")

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
                    neighbor = cls.instance_ref_grid.grid.get((nx, ny))
                    if neighbor and neighbor not in visited:
                        # Apply passable or climbable checks
                        if check_passable and not neighbor.is_passable():
                            continue
                        if climbable and not neighbor.get_climbable():
                            continue
                        visited.add(neighbor)
                        queue.append((neighbor, dist + 1))

        return result

    @classmethod
    def astar(cls, start: "BaseTile", goal: "BaseTile", movement_speed: float) -> Optional[List["BaseTile"]]:
        r"""
        A* search algorithm for pathfinding on a hex grid.

        Uses:
          - g(n): cost from start to current node.
          - h(n): heuristic estimated cost from current node to goal (via heuristic_tiles).
          - f(n) = g(n) + h(n): total cost estimate.

        Process:
          1. Initialize the open set with the start node.
          2. Loop until the open set is empty:
             a. Extract the node with the lowest f(n).
             b. If this node is the goal, reconstruct and return the path.
             c. Otherwise, for each neighbor:
                i. Calculate tentative g(n) = current g(n) + (neighbor.movement_cost / movement_speed).
                ii. If this path is better, update the cost and record the parent.

        ASCII Diagram:

             [Start]
                |
              (expanding)
                |
             [Tile] ---> ... ---> [Goal]

        :param start: The starting Tile.
        :param goal: The target Tile.
        :param movement_speed: Movement speed factor for cost adjustment.
        :return: List of Tiles representing the path from start to goal, or None if no path exists.
        """
        open_set = []
        heappush(open_set, (0, id(start), start))  # Use id(start) for unique sorting
        came_from: Dict["BaseTile", "BaseTile"] = {}
        g_score: Dict["BaseTile", float] = {start: 0.0}
        f_score: Dict["BaseTile", float] = {start: cls.heuristic_tiles(start, goal)}

        while open_set:
            _, __, current = heappop(open_set)  # Extract current safely

            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]

            for neighbor in cls.get_neighbors(current, check_passable=True):
                tentative_g_score = g_score[current] + (neighbor.movement_cost / movement_speed)

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + cls.heuristic_tiles(neighbor, goal)
                    heappush(open_set, (f_score[neighbor], id(neighbor), neighbor))  # Use id() for tie-breaking

        return None  # No path found

    @classmethod
    def dijkstra(cls, start: "BaseTile", goal: "BaseTile") -> Optional[List["BaseTile"]]:
        r"""
        Dijkstra's algorithm for the shortest path with weighted movement.

        This algorithm does not use a heuristic; it expands nodes based on cumulative cost.

        Process:
          1. Begin with the starting tile at cost 0.
          2. Iteratively update costs to neighbors.
          3. Once the goal is reached, reconstruct and return the path.

        ASCII Diagram:

             [Start]
                |
           (cost += movement_cost)
                |
             [Tile] ---> ... ---> [Goal]

        :param start: The starting Tile.
        :param goal: The target Tile.
        :return: List of Tiles representing the path, or None if unreachable.
        """
        open_set = []
        heappush(open_set, (0, start))
        came_from: Dict["BaseTile", "BaseTile"] = {}
        cost_so_far: Dict["BaseTile", float] = {start: 0.0}

        while open_set:
            current_cost, current = heappop(open_set)

            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]

            for neighbor in cls.get_neighbors(current):
                new_cost = cost_so_far[current] + neighbor.movement_cost
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    heappush(open_set, (new_cost, neighbor))
                    came_from[neighbor] = current

        return None  # No path found

    @classmethod
    def has_line_of_sight(cls, tile_a: "BaseTile", tile_b: "BaseTile") -> bool:
        r"""
        Determines if there is a direct, unobstructed path between two tiles using Bresenham's Line Algorithm.

        Traces a straight line from tile_a to tile_b. If any tile along the line has a movement_cost
        above a certain threshold (e.g., impassable terrain), the function returns False.

        ASCII Diagram:

              (x0,y0) *
                        \
                         \
                          *  <-- (x1,y1)

        :param tile_a: Starting tile.
        :param tile_b: Ending tile.
        :return: True if the path is clear; otherwise, False.
        """
        x0, y0 = tile_a.x, tile_a.y
        x1, y1 = tile_b.x, tile_b.y

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while (x0, y0) != (x1, y1):
            if (x0, y0) in cls.instance_ref_grid.grid:
                tile: "BaseTile" = cls.instance_ref_grid.grid[(x0, y0)]
                if tile.movement_cost > 10:  # Threshold for impassable terrain.
                    return False

            e2 = err * 2
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

        return True

    @classmethod
    def bidirectional_dijkstra(cls, start: "BaseTile", goal: "BaseTile") -> Optional[List["BaseTile"]]:
        r"""
        Bidirectional Dijkstra's algorithm for efficient pathfinding.

        Two searches are initiated simultaneously from the start and goal. When the searches meet,
        the full path is reconstructed.

        ASCII Diagram:

           Start  <---->  Goal
               \        /
                \  Meet/
                 \----/

        Process:
          1. Initialize open sets and cost dictionaries for both directions.
          2. Expand nodes from both sides alternately.
          3. When a node is reached by both searches, reconstruct the complete path.

        :param start: The starting Tile.
        :param goal: The target Tile.
        :return: Combined path as a list of Tiles, or None if no path exists.
        """
        open_start = []
        open_goal = []
        heappush(open_start, (0, start))
        heappush(open_goal, (0, goal))
        came_from_start: Dict["BaseTile", "BaseTile"] = {}
        came_from_goal: Dict["BaseTile", "BaseTile"] = {}
        cost_start: Dict["BaseTile", float] = {start: 0.0}
        cost_goal: Dict["BaseTile", float] = {goal: 0.0}

        meeting_node = None
        while open_start and open_goal:
            _, current_start = heappop(open_start)
            _, current_goal = heappop(open_goal)

            if current_start in cost_goal or current_goal in cost_start:
                meeting_node = current_start if current_start in cost_goal else current_goal
                break

            for neighbor in cls.get_neighbors(current_start):
                new_cost = cost_start[current_start] + neighbor.movement_cost
                if neighbor not in cost_start or new_cost < cost_start[neighbor]:
                    cost_start[neighbor] = new_cost
                    heappush(open_start, (new_cost, neighbor))
                    came_from_start[neighbor] = current_start

            for neighbor in cls.get_neighbors(current_goal):
                new_cost = cost_goal[current_goal] + neighbor.movement_cost
                if neighbor not in cost_goal or new_cost < cost_goal[neighbor]:
                    cost_goal[neighbor] = new_cost
                    heappush(open_goal, (new_cost, neighbor))
                    came_from_goal[neighbor] = current_goal

        if meeting_node is None:
            return None  # No meeting point found.

        # Reconstruct path from start to meeting node.
        path_start = []
        current = meeting_node
        while current in came_from_start:
            path_start.append(current)
            current = came_from_start[current]
        path_start.append(start)
        path_start.reverse()

        # Reconstruct path from meeting node to goal.
        path_goal = []
        current = meeting_node
        while current in came_from_goal:
            current = came_from_goal[current]
            path_goal.append(current)

        return path_start + path_goal

    @classmethod
    def theta_star(
        cls, start: "BaseTile", goal: "BaseTile", check_passable: bool = True, check_swimmable: bool = False
    ) -> Optional[List["BaseTile"]]:
        r"""
        Theta* algorithm for any-angle pathfinding on a hex grid.

        Theta* extends A* by allowing shortcuts between non-adjacent nodes if there is a clear line-of-sight.

        Process:
          1. Use a priority queue similar to A*.
          2. For each neighbor of the current node, check if the parent of the current node has a direct
             line-of-sight to the neighbor.
          3. Use the parent's cost if a clear path exists, otherwise use the current node's cost.
          4. Update path data if a lower cost path is found.

        ASCII Diagram:

             Parent ------+
                  \      |
                   \     |
                [Current] ---> [Neighbor]

        :param start: Starting Tile.
        :param goal: Target Tile.
        :param check_passable: If True, only consider passable tiles.
        :param check_swimmable: If True, only consider swimmable tiles.
        :return: List of Tiles representing the path from start to goal, or None if no path exists.
        """
        open_set = []
        heappush(open_set, (0, start))
        came_from: Dict["BaseTile", "BaseTile"] = {}
        g_score: Dict["BaseTile", float] = {start: 0.0}
        f_score: Dict["BaseTile", float] = {start: cls.heuristic(start, goal)}

        while open_set:
            _, current = heappop(open_set)

            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]

            for neighbor in cls.get_neighbors(current, check_passable, check_swimmable):
                parent = came_from.get(current, start)
                if cls.has_line_of_sight(parent, neighbor):
                    tentative_g_score = g_score[parent] + neighbor.movement_cost
                else:
                    tentative_g_score = g_score[current] + neighbor.movement_cost

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + cls.heuristic(neighbor, goal)
                heappush(open_set, (f_score[neighbor], neighbor))

        return None  # No path found

    @staticmethod
    def hex_distance(tile1: BaseTile, tile2: BaseTile) -> int:
        """Calculate the hex grid distance between two tiles."""
        return (abs(tile1.x - tile2.x) + abs(tile1.y - tile2.y)) // 2
