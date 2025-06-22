import math
import random
import time
import functools
from itertools import combinations
from typing import TYPE_CHECKING, Any, Callable, Dict, Tuple, Type, TypeVar, Generic, Optional, List


if TYPE_CHECKING:
    from system.generators.basic import Hex
from system.subsystems.hexgen.enums import HexEdge

# -------------------- Memoization --------------------

F = TypeVar("F", bound=Callable[..., Any])


class memoized(Generic[F]):
    """Decorator. Caches a function's return value each time it is called."""

    def __init__(self, func: F):
        self.func = func
        self.cache: Dict[Tuple[Any, ...], Any] = {}

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        key = args + tuple(sorted(kwargs.items()))
        if key in self.cache:
            return self.cache[key]
        value = self.func(*args, **kwargs)
        self.cache[key] = value
        return value

    def __repr__(self) -> str:
        return self.func.__doc__ or ""

    def __get__(self, obj: Any, objtype: Any) -> Callable[..., Any]:
        return functools.partial(self.__call__, obj)


# -------------------- Utility Functions --------------------


def latitude_to_number(latitude: int, map_size: int) -> float:
    """Converts latitude in degrees to a normalized grid position."""
    return (map_size / 2) - ((latitude / 90) * (map_size / 2))


def pressure_at_seasons(latitude: float, base_pressure: float, pressure_diff: float, itcz_rise: float) -> float:
    itcz = (-10 + itcz_rise, 10 + itcz_rise)
    sthz = {"north": (20 + itcz_rise, 40 + itcz_rise), "south": (-40 + itcz_rise, -20 + itcz_rise)}
    pf = {"north": (50 + itcz_rise, 70 + itcz_rise), "south": (-70 + itcz_rise, -50 + itcz_rise)}
    final_pressure: float
    if itcz[0] <= latitude <= itcz[1]:
        final_pressure = base_pressure - (-math.pow(latitude - itcz_rise, 2) + 100) * (pressure_diff / 100)
    elif sthz["south"][0] <= latitude <= sthz["south"][1]:
        final_pressure = base_pressure + ((-math.pow(latitude + (30 - itcz_rise), 2) + 100) / 100) * pressure_diff
    elif sthz["north"][0] <= latitude <= sthz["north"][1]:
        final_pressure = base_pressure + ((-math.pow(latitude - (30 + itcz_rise), 2) + 100) / 100) * pressure_diff
    elif pf["south"][0] <= latitude <= pf["south"][1]:
        final_pressure = base_pressure - ((-math.pow(latitude + (60 - itcz_rise), 2) + 100) / 100) * (pressure_diff / 2)
    elif pf["north"][0] <= latitude <= pf["north"][1]:
        final_pressure = base_pressure - ((-math.pow(latitude - (60 + itcz_rise), 2) + 100) / 100) * (pressure_diff / 2)
    else:
        final_pressure = base_pressure + random.randint(-1, 1)
    return round(final_pressure, 2)


@memoized
def clockwise_hex_edge(hex_edge: HexEdge, reverse: bool = False) -> HexEdge:
    if hex_edge is HexEdge.east:
        return HexEdge.south_east if not reverse else HexEdge.north_east
    elif hex_edge is HexEdge.south_east:
        return HexEdge.south_west if not reverse else HexEdge.east
    elif hex_edge is HexEdge.south_west:
        return HexEdge.west if not reverse else HexEdge.south_east
    elif hex_edge is HexEdge.west:
        return HexEdge.north_west if not reverse else HexEdge.south_west
    elif hex_edge is HexEdge.north_west:
        return HexEdge.north_east if not reverse else HexEdge.west
    elif hex_edge is HexEdge.north_east:
        return HexEdge.east if not reverse else HexEdge.north_west
    raise ValueError(f"Invalid hex_edge: {hex_edge}")


class Timer:
    def __init__(self, text: str, debug: bool = True) -> None:
        self.text = text
        self.debug = debug
        self.start: float = 0.0
        self.end: float = 0.0
        self.interval: float = 0.0

    def __enter__(self) -> "Timer":
        if self.debug:
            print(self.text.ljust(50), end="")
            print("starting...")
        self.start = time.perf_counter()
        return self

    def __exit__(
        self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], traceback: Optional[Any]
    ) -> None:
        self.end = time.perf_counter()
        self.interval = self.end - self.start
        if self.debug:
            print(self.text.ljust(50), end="")
            print("finished after {:0.03f} ms\n".format(self.interval * 1000))


@memoized
def is_opposite_hex(my_side: HexEdge, other_side: HexEdge, strict: bool = False) -> bool:
    opp: Dict[HexEdge, List[HexEdge]] = {
        HexEdge.west: [HexEdge.east, HexEdge.north_east, HexEdge.south_east],
        HexEdge.north_west: [HexEdge.south_east, HexEdge.east, HexEdge.south_west],
        HexEdge.north_east: [HexEdge.south_west, HexEdge.south_east, HexEdge.west],
        HexEdge.east: [HexEdge.west, HexEdge.north_west, HexEdge.south_west],
        HexEdge.south_east: [HexEdge.north_west, HexEdge.north_east, HexEdge.west],
        HexEdge.south_west: [HexEdge.north_east, HexEdge.east, HexEdge.north_west],
    }
    if strict:
        return other_side is opp[my_side][0]
    return other_side in opp[my_side]


def is_isthmus(h: "Hex") -> bool:
    if h.is_water:
        return False
    water_neighbors = [x for x in h.neighbors if x[1].is_water]
    if len(water_neighbors) == 2:
        for one, two in combinations(water_neighbors, 2):
            if is_opposite_hex(one[0], two[0]):
                return True
    return False


def is_peninsula(h: "Hex") -> bool:
    if h.is_water:
        return False
    land_neighbors = [x for x in h.neighbors if x[1].is_land]
    return len(land_neighbors) == 1


def is_bay(h: "Hex") -> bool:
    if h.is_land:
        return False
    water_neighbors = [x for x in h.neighbors if x[1].is_water]
    return len(water_neighbors) == 1


def is_strait(h: "Hex") -> bool:
    if h.is_land:
        return False
    water_neighbors = [x for x in h.neighbors if x[1].is_water]
    if len(water_neighbors) == 2:
        return is_opposite_hex(water_neighbors[0][0], water_neighbors[1][0])
    return False


def first_hex_without_geoform(hexes: List[List["Hex"]]) -> Optional["Hex"]:
    for y, row in enumerate(hexes):
        for x, h in enumerate(row):
            if h.geoform_type is None:
                return h
    return None
