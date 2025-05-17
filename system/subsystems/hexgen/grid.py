import math
import numpy as np
from typing import Any, Dict, List

from system.subsystems.hexgen.hex import Hex
from system.subsystems.hexgen.heightmap import Heightmap


class GridBoundsException(Exception):
    pass


class Grid:
    def __init__(self, heightmap: Heightmap, params: Dict[str, Any], debug: bool = False):
        self.heightmap: Heightmap = heightmap
        self.sealevel: float = heightmap.sealevel
        self.params: Dict[str, Any] = params
        self.average_height: float = heightmap.average_height
        self.highest_height: float = heightmap.highest_height
        self.lowest_height: float = heightmap.lowest_height

        self.avg_altitude: float = 0.0

        self.hexes: List[Hex] = []
        self.coldest_hexes: List[Hex] = []

        if debug:
            print("Making grid")

        self.num_ocean_hexes: int = 0

        self.grid: np.ndarray[Any, Any] = np.ndarray((self.heightmap.size, self.heightmap.size), dtype=object)

        for y, row in enumerate(self.grid):
            for x, _ in enumerate(row):
                self.grid[x][y] = Hex(self, x, y, self.heightmap.height_at(x, y))
                if self.grid[x][y].is_water:
                    self.num_ocean_hexes += 1

        self.calculate()

    @property
    def size(self) -> int:
        return self.params.get("size", 100)

    def get(self, x: int, y: int) -> Hex | None:
        """
        Returns the Hex at (x, y) or None if out of bounds.
        """
        return self.find_hex(x, y)

    def find_hex(self, x: int, y: int) -> Hex:
        """Finds a hex at (x, y) coordinates."""
        try:
            return self.grid[x][y]
        except IndexError:
            raise GridBoundsException(f"Invalid coordinates {x}, {y}")

    def calculate(self) -> None:
        # Run through the grid, calculate the edges, compute averages
        alt: float = 0.0
        hexes: List[Hex] = []
        for y, row in enumerate(self.grid):
            for x, _ in enumerate(row):
                self.grid[x][y].calculate()
                alt += self.grid[x][y].altitude
                hexes.append(self.grid[x][y])
        self.avg_altitude = round(alt / math.pow(self.size, 2))
        self.hexes = sorted(hexes, key=lambda h: h.temperature)

        number: int = round(len(self.hexes) * 0.10)
        self.coldest_hexes = self.hexes[:number]

    def hex_distance(self, a: tuple[int, int], b: tuple[int, int]) -> int:
        ax, ay = a
        bx, by = b
        az = -ax - ay
        bz = -bx - by
        return max(abs(ax - bx), abs(ay - by), abs(az - bz))

    def straight_line_path(self, a: tuple[int, int], b: tuple[int, int]) -> list[tuple[int, int]]:
        def lerp(a, b, t):
            return a + (b - a) * t

        def cube_lerp(a, b, t):
            return (lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t))

        def cube_round(cube):
            rx = round(cube[0])
            ry = round(cube[1])
            rz = round(cube[2])

            x_diff = abs(rx - cube[0])
            y_diff = abs(ry - cube[1])
            z_diff = abs(rz - cube[2])

            if x_diff > y_diff and x_diff > z_diff:
                rx = -ry - rz
            elif y_diff > z_diff:
                ry = -rx - rz
            else:
                rz = -rx - ry
            return (int(rx), int(ry), int(rz))

        ax, ay = a
        bx, by = b
        ac = (ax, ay, -ax - ay)
        bc = (bx, by, -bx - by)

        N = self.hex_distance(a, b)
        results = []
        for i in range(N + 1):
            t = 0 if N == 0 else i / N
            cube = cube_lerp(ac, bc, t)
            rx, ry, rz = cube_round(cube)
            results.append((rx, ry))
        return results
