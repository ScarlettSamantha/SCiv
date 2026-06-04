# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false

from dataclasses import dataclass
from pathlib import Path
import importlib
import sys


ROOT = Path(__file__).resolve().parents[1]
SCIV_ROOT = ROOT / "sciv"
if str(SCIV_ROOT) not in sys.path:
    sys.path.insert(0, str(SCIV_ROOT))

landmass_label_overlay = importlib.import_module("system.renderers.landmass_label_overlay")
zoom_visibility = importlib.import_module("system.zoom_visibility")

build_landmass_label_specs = landmass_label_overlay.build_landmass_label_specs
build_territory_label_specs = landmass_label_overlay.build_territory_label_specs
spread_label_text = landmass_label_overlay.spread_label_text
territory_label_text = landmass_label_overlay.territory_label_text
ZoomVisibilityRule = zoom_visibility.ZoomVisibilityRule
compute_zoom_visibility_alpha = zoom_visibility.compute_zoom_visibility_alpha


@dataclass(slots=True)
class DummyTile:
    x: int
    y: int
    pos_x: float
    pos_y: float
    pos_z: float
    landmass_name: str | None = None
    landmass_type: str | None = None
    landmass_size: int | None = None
    territory_id: int | None = None
    territory_name: str | None = None
    territory_size: int | None = None
    territory_is_anchor: bool = False


def test_compute_zoom_visibility_alpha_fades_in_for_zoomed_out_overlays() -> None:
    rule = ZoomVisibilityRule(min_zoom=30.0, fade_in=10.0)

    assert compute_zoom_visibility_alpha(19.5, rule) == 0.0
    assert compute_zoom_visibility_alpha(25.0, rule) == 0.5
    assert compute_zoom_visibility_alpha(30.0, rule) == 1.0
    assert compute_zoom_visibility_alpha(44.0, rule) == 1.0


def test_compute_zoom_visibility_alpha_supports_zoomed_in_only_surfaces() -> None:
    rule = ZoomVisibilityRule(max_zoom=18.0, fade_out=6.0)

    assert compute_zoom_visibility_alpha(12.0, rule) == 1.0
    assert compute_zoom_visibility_alpha(21.0, rule) == 0.5
    assert compute_zoom_visibility_alpha(24.0, rule) == 0.0


def test_build_landmass_label_specs_groups_named_regions_and_skips_tiny_islands() -> None:
    tiles = [
        DummyTile(0, 0, 0.0, 0.0, 0.0, landmass_name="Aurelia", landmass_type="Continent", landmass_size=30),
        DummyTile(1, 0, 2.0, 0.0, 0.0, landmass_name="Aurelia", landmass_type="Continent", landmass_size=30),
        DummyTile(2, 0, 4.0, 0.0, 0.0, landmass_name="Aurelia", landmass_type="Continent", landmass_size=30),
        DummyTile(9, 9, 9.0, 9.0, 0.0, landmass_name="Pebble Cay", landmass_type="Small Island", landmass_size=4),
    ]

    specs = build_landmass_label_specs(tiles, min_landmass_size=12)

    assert len(specs) == 1
    assert specs[0].name == "Aurelia"
    assert specs[0].display_text == "A U R E L I A"
    assert specs[0].anchor == (2.0, 0.0, 2.3)


def test_spread_label_text_preserves_word_boundaries() -> None:
    assert spread_label_text("Golden Reach") == "G O L D E N   R E A C H"


def test_territory_label_text_keeps_compact_uppercase_words() -> None:
    assert territory_label_text("Green March") == "GREEN MARCH"


def test_build_territory_label_specs_groups_named_regions_and_prefers_anchor_tile() -> None:
    tiles = [
        DummyTile(
            0,
            0,
            0.0,
            0.0,
            0.0,
            territory_id=2,
            territory_name="Green March",
            territory_size=18,
        ),
        DummyTile(
            1,
            0,
            2.0,
            0.0,
            0.0,
            territory_id=2,
            territory_name="Green March",
            territory_size=18,
            territory_is_anchor=True,
        ),
        DummyTile(
            2,
            0,
            4.0,
            0.0,
            0.0,
            territory_id=2,
            territory_name="Green March",
            territory_size=18,
        ),
        DummyTile(
            8,
            8,
            8.0,
            8.0,
            0.0,
            territory_id=5,
            territory_name="Tiny Vale",
            territory_size=4,
            territory_is_anchor=True,
        ),
    ]

    specs = build_territory_label_specs(tiles, min_territory_size=8)

    assert len(specs) == 1
    assert specs[0].name == "Green March"
    assert specs[0].display_text == "GREEN MARCH"
    assert specs[0].anchor == (2.0, 0.0, 2.05)
