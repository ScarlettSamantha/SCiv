from pathlib import Path
import importlib
import random
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCIV_ROOT = ROOT / "sciv"
if str(SCIV_ROOT) not in sys.path:
    sys.path.insert(0, str(SCIV_ROOT))

territory_generation: Any = importlib.import_module("system.subsystems.hexgen.territory_generation")
TerritoryGenerationContext = territory_generation.TerritoryGenerationContext
generate_territories = territory_generation.generate_territories
territory_seed_score = territory_generation._territory_seed_score
territory_step_cost = territory_generation._territory_step_cost


class DummyBiome:
    def __init__(self, name: str, title: str | None = None):
        self.name = name
        self.title = title or name.replace("_", " ").title()


class DummyEdge:
    def __init__(self, *, is_river: bool = False):
        self.is_river = is_river


class DummyHex:
    def __init__(
        self,
        x: int,
        y: int,
        *,
        altitude: float = 12.0,
        moisture: float = 4.0,
        distance: float = 2.0,
        temperature: float = 12.0,
        biome_name: str = "grasslands",
    ):
        self.x = x
        self.y = y
        self.altitude = altitude
        self.moisture = moisture
        self.distance = distance
        self._temperature = (temperature, temperature)
        self.biome = DummyBiome(biome_name)
        self.territory = None
        self.marked = False
        self._neighbors: list[tuple[str, "DummyHex"]] = []
        self._edge_by_neighbor: dict[DummyHex, DummyEdge] = {}
        self._side_by_neighbor: dict[DummyHex, str] = {}

    @property
    def temperature(self) -> tuple[float, float]:
        return self._temperature

    @property
    def is_land(self) -> bool:
        return self.altitude >= 0.0

    @property
    def is_water(self) -> bool:
        return not self.is_land

    @property
    def neighbors(self) -> list[tuple[str, "DummyHex"]]:
        return self._neighbors

    @property
    def surrounding(self) -> list["DummyHex"]:
        return [neighbor for _, neighbor in self._neighbors]

    @property
    def map_surrounding(self) -> list["DummyHex"]:
        return self.surrounding

    @property
    def edges(self) -> list[DummyEdge]:
        return list(self._edge_by_neighbor.values())

    @property
    def is_coast_land(self) -> bool:
        return self.is_land and any(neighbor.is_water for _, neighbor in self._neighbors)

    def connect(self, other: "DummyHex", *, river: bool = False) -> None:
        side_to_other = f"to_{other.x}_{other.y}"
        side_to_self = f"to_{self.x}_{self.y}"
        edge = DummyEdge(is_river=river)

        self._neighbors.append((side_to_other, other))
        other._neighbors.append((side_to_self, self))
        self._edge_by_neighbor[other] = edge
        other._edge_by_neighbor[self] = edge
        self._side_by_neighbor[other] = side_to_other
        other._side_by_neighbor[self] = side_to_self

    def get_side_to(self, target_hex: "DummyHex") -> str | None:
        return self._side_by_neighbor.get(target_hex)

    def get_edge(self, side: str | None) -> DummyEdge | None:
        if side is None:
            return None
        for neighbor, neighbor_side in self._side_by_neighbor.items():
            if neighbor_side == side:
                return self._edge_by_neighbor[neighbor]
        return None

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DummyHex):
            return NotImplemented
        return self.x == other.x and self.y == other.y


class DummyGrid:
    def __init__(self, hexes: list[DummyHex], *, sealevel: float = 0.0):
        self.hexes = hexes
        self.sealevel = sealevel


class DummyMapGen:
    def __init__(self, hexes: list[DummyHex], *, num_territories: int, seed: int = 7):
        self.debug = False
        self.params = {"num_territories": num_territories}
        self.rng = random.Random(seed)
        self.hex_grid = DummyGrid(hexes)
        self.territories: list[Any] = []

    def _local_ruggedness(self, hex_tile: DummyHex) -> float:
        diffs = [abs(float(hex_tile.altitude) - float(neighbor.altitude)) for _, neighbor in hex_tile.neighbors]
        return sum(diffs) / max(1, len(diffs))

    def hex_distance(self, a: tuple[int, int], b: tuple[int, int]) -> int:
        aq, ar = a
        bq, br = b
        return (abs(aq - bq) + abs(aq + ar - bq - br) + abs(ar - br)) // 2


def _build_chain(start_x: int, length: int) -> list[DummyHex]:
    chain = [DummyHex(start_x + index, 0, distance=3.0) for index in range(length)]
    for left, right in zip(chain, chain[1:], strict=False):
        left.connect(right)
    return chain


def test_territory_step_cost_penalizes_river_crossings() -> None:
    current = DummyHex(0, 0)
    plain_neighbor = DummyHex(0, 1)
    river_neighbor = DummyHex(1, 0)

    current.connect(plain_neighbor)
    current.connect(river_neighbor, river=True)

    mapgen = DummyMapGen([current, plain_neighbor, river_neighbor], num_territories=0)
    context = TerritoryGenerationContext(mapgen=mapgen)

    plain_cost = territory_step_cost(context, current, plain_neighbor)
    river_cost = territory_step_cost(context, current, river_neighbor)

    assert river_cost > plain_cost + 3.0


def test_territory_seed_score_prefers_valleys_over_rugged_peaks() -> None:
    valley = DummyHex(0, 0, altitude=14.0, moisture=7.0, distance=2.0, temperature=14.0)
    valley_a = DummyHex(0, 1, altitude=13.5, moisture=7.0, distance=2.0, temperature=14.0)
    valley_b = DummyHex(1, 0, altitude=14.5, moisture=7.0, distance=2.0, temperature=14.0)
    valley.connect(valley_a, river=True)
    valley.connect(valley_b)

    peak = DummyHex(5, 5, altitude=138.0, moisture=1.0, distance=6.0, temperature=-12.0)
    peak_a = DummyHex(5, 6, altitude=56.0, moisture=1.0, distance=6.0, temperature=-8.0)
    peak_b = DummyHex(6, 5, altitude=42.0, moisture=1.0, distance=6.0, temperature=-10.0)
    peak.connect(peak_a)
    peak.connect(peak_b)

    mapgen = DummyMapGen([valley, valley_a, valley_b, peak, peak_a, peak_b], num_territories=0)
    context = TerritoryGenerationContext(mapgen=mapgen)

    assert territory_seed_score(context, valley) > territory_seed_score(context, peak)


def test_generate_territories_keeps_large_land_components_separate() -> None:
    large_component = _build_chain(0, 14)
    other_large_component = _build_chain(100, 12)
    mapgen = DummyMapGen([*large_component, *other_large_component], num_territories=1, seed=11)

    generate_territories(mapgen)

    first_component_territories = {hex_tile.territory.id for hex_tile in large_component if hex_tile.territory is not None}
    second_component_territories = {
        hex_tile.territory.id for hex_tile in other_large_component if hex_tile.territory is not None
    }

    assert len(mapgen.territories) == 2
    assert len(first_component_territories) == 1
    assert len(second_component_territories) == 1
    assert first_component_territories != second_component_territories


def test_generate_territories_assigns_unique_names() -> None:
    first_component = _build_chain(0, 10)
    second_component = _build_chain(100, 10)
    mapgen = DummyMapGen([*first_component, *second_component], num_territories=2, seed=23)

    generate_territories(mapgen)

    names = [territory.name for territory in mapgen.territories]

    assert all(isinstance(name, str) and name.strip() for name in names)
    assert len(set(names)) == len(names)
