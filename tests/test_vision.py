# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false

from dataclasses import dataclass, field
from pathlib import Path
import importlib
import sys


ROOT = Path(__file__).resolve().parents[1]
SCIV_ROOT = ROOT / "sciv"
if str(SCIV_ROOT) not in sys.path:
    sys.path.insert(0, str(SCIV_ROOT))

vision_module = importlib.import_module("gameplay.vision")

Vision = vision_module.Vision
VisionTileState = vision_module.VisionTileState
collect_radius_visibility = vision_module.collect_radius_visibility
expand_border_visibility = vision_module.expand_border_visibility


@dataclass(eq=False)
class DummyTerrain:
    name: str


@dataclass(eq=False)
class DummyResourceBag:
    values: dict[str, object] = field(default_factory=lambda: {})

    def flatten(self) -> dict[str, object]:
        return self.values


@dataclass(eq=False)
class DummyTile:
    tag: str
    neighbors_by_radius: dict[int, list["DummyTile"]] = field(default_factory=lambda: {})
    direct_neighbors: list["DummyTile"] = field(default_factory=lambda: [])
    city: object | None = None
    units: list[object] = field(default_factory=lambda: [])
    improvements: list[object] = field(default_factory=lambda: [])
    resources: DummyResourceBag = field(default_factory=DummyResourceBag)
    terrain: DummyTerrain = field(default_factory=lambda: DummyTerrain("plains"))

    def __hash__(self) -> int:
        return hash(self.tag)

    def get_tag(self) -> str:
        return self.tag

    def get_units(self) -> list[object]:
        return self.units

    def get_improvements(self) -> list[object]:
        return self.improvements

    def get_terrain(self) -> DummyTerrain:
        return self.terrain


def test_collect_radius_visibility_includes_origin_and_neighbors() -> None:
    origin = DummyTile("origin")
    neighbor_a = DummyTile("a")
    neighbor_b = DummyTile("b")
    origin.neighbors_by_radius[2] = [neighbor_a, neighbor_b]

    visible = collect_radius_visibility(origin, 2, lambda tile, radius: tile.neighbors_by_radius.get(radius, []))

    assert visible == {origin, neighbor_a, neighbor_b}


def test_expand_border_visibility_grows_rings_from_owned_tiles() -> None:
    center = DummyTile("center")
    first_ring = DummyTile("first")
    second_ring = DummyTile("second")
    center.direct_neighbors = [first_ring]
    first_ring.direct_neighbors = [center, second_ring]
    second_ring.direct_neighbors = [first_ring]

    visible = expand_border_visibility({center}, 2, lambda tile: tile.direct_neighbors)

    assert visible == {center, first_ring, second_ring}


def test_vision_recompute_lingers_then_fogs_tiles() -> None:
    first = DummyTile("first")
    second = DummyTile("second")
    vision = Vision(linger_turns=2)

    vision.recompute_visible_tiles({first, second}, linger_turns=2)
    assert vision.get_tile_state(first) is VisionTileState.VISIBLE
    assert vision.get_tile_state(second) is VisionTileState.VISIBLE

    vision.recompute_visible_tiles({first}, linger_turns=2)
    assert vision.get_tile_state(second) is VisionTileState.LINGERING
    assert vision.get_turns_remaining(second) == 2
    assert vision.is_visible(second) is True

    vision.recompute_visible_tiles({first}, linger_turns=2)
    assert vision.get_tile_state(second) is VisionTileState.LINGERING
    assert vision.get_turns_remaining(second) == 1

    vision.recompute_visible_tiles({first}, linger_turns=2)
    assert vision.get_tile_state(second) is VisionTileState.FOGGED
    assert vision.get_turns_remaining(second) == 0
    assert vision.is_visible(second) is False
    assert vision.is_explored(second) is True


def test_vision_load_state_supports_legacy_and_structured_formats() -> None:
    legacy_vision = Vision()
    legacy_vision.load_state(["tile_1", "tile_2"])

    assert legacy_vision.get_tile_state("tile_1") is VisionTileState.VISIBLE
    assert legacy_vision.get_tile_state("tile_2") is VisionTileState.VISIBLE

    structured_vision = Vision()
    structured_vision.load_state(
        {
            "linger_turns": 4,
            "tiles": [
                {"tile_tag": "tile_3", "state": "lingering", "turns_remaining": 2},
                {"tile_tag": "tile_4", "state": "fogged", "turns_remaining": 0},
            ],
        }
    )

    assert structured_vision.get_default_linger_turns() == 4
    assert structured_vision.get_tile_state("tile_3") is VisionTileState.LINGERING
    assert structured_vision.get_turns_remaining("tile_3") == 2
    assert structured_vision.get_tile_state("tile_4") is VisionTileState.FOGGED


def test_vision_reveal_sources_collect_runtime_reveal_tags() -> None:
    first = DummyTile("first")
    vision = Vision()

    assert vision.set_reveal_source("obelisk", [first, "second"]) is True
    assert vision.get_reveal_tile_tags() == {"first", "second"}

    assert vision.set_reveal_source("obelisk", [first, "second"]) is False
    assert vision.clear_reveal_source("obelisk") is True
    assert vision.get_reveal_tile_tags() == set()
