from dataclasses import dataclass, field

from pathlib import Path
import importlib
import sys


ROOT = Path(__file__).resolve().parents[1]
SCIV_ROOT = ROOT / "sciv"
if str(SCIV_ROOT) not in sys.path:
    sys.path.insert(0, str(SCIV_ROOT))

fog_module = importlib.import_module("system.renderers.fog_of_war")
vision_module = importlib.import_module("gameplay.vision")

FogOfWarController = fog_module.FogOfWarController
FOGGED_TILE_TINT = fog_module.FOGGED_TILE_TINT
VisionTileState = vision_module.VisionTileState


@dataclass
class DummyRenderer:
    states: list[VisionTileState] = field(default_factory=lambda: [])
    fog_ceilings: list[float] = field(default_factory=lambda: [])

    def set_fog_ceiling_z(self, fog_ceiling_z: float) -> None:
        self.fog_ceilings.append(fog_ceiling_z)

    def set_visibility_state(self, state: VisionTileState) -> None:
        self.states.append(state)


@dataclass(eq=False)
class DummyTile:
    tag: str
    pos_z: float = 0.0
    renderer: DummyRenderer = field(default_factory=DummyRenderer)

    def get_tag(self) -> str:
        return self.tag


@dataclass
class DummyVision:
    states: dict[str, VisionTileState]
    visible_tags: set[str]
    explored_tags: set[str]

    def get_tile_state(self, tile_or_tag: str) -> VisionTileState:
        return self.states.get(tile_or_tag, VisionTileState.UNSEEN)

    def get_visible_tile_tags(self) -> set[str]:
        return set(self.visible_tags)

    def get_explored_tile_tags(self) -> set[str]:
        return set(self.explored_tags)


@dataclass
class DummyPlayer:
    vision: DummyVision
    tag: str = "player.session"


@dataclass
class DummyTileGrid:
    shown: list[str] = field(default_factory=lambda: [])
    hidden: list[str] = field(default_factory=lambda: [])
    tinted: dict[str, tuple[float, float, float, float]] = field(default_factory=lambda: {})
    cleared: list[str] = field(default_factory=lambda: [])
    collect_calls: int = 0

    def hide_tile(self, tile_or_index: DummyTile) -> None:
        self.hidden.append(tile_or_index.tag)

    def show_tile(self, tile_or_index: DummyTile) -> None:
        self.shown.append(tile_or_index.tag)

    def set_tile_tint(self, tile_or_index: DummyTile, rgba: tuple[float, float, float, float]) -> None:
        self.tinted[tile_or_index.tag] = rgba

    def clear_tile_tint(self, tile_or_index: DummyTile) -> None:
        self.cleared.append(tile_or_index.tag)
        self.tinted.pop(tile_or_index.tag, None)

    def collect(self) -> None:
        self.collect_calls += 1

    def get_max_world_z(self) -> float:
        return 3.5


@dataclass
class DummyTileOverlay:
    shown: list[str] = field(default_factory=lambda: [])
    hidden: list[str] = field(default_factory=lambda: [])

    def hide_tile(self, tile: DummyTile) -> None:
        self.hidden.append(tile.tag)

    def show_tile(self, tile: DummyTile) -> None:
        self.shown.append(tile.tag)


@dataclass
class DummyUnit:
    tile: DummyTile
    visible: bool | None = None

    def get_tile(self) -> DummyTile:
        return self.tile

    def set_render_visibility(self, visible: bool) -> None:
        self.visible = visible


@dataclass
class DummyRoot:
    shown: bool = False
    hidden: bool = False

    def show(self) -> None:
        self.shown = True
        self.hidden = False

    def hide(self) -> None:
        self.hidden = True
        self.shown = False


@dataclass
class DummyLabelOverlay:
    root: DummyRoot = field(default_factory=DummyRoot)


def test_fog_controller_applies_visible_fogged_and_unseen_states() -> None:
    controller = FogOfWarController()
    visible_tile = DummyTile("visible")
    fogged_tile = DummyTile("fogged")
    unseen_tile = DummyTile("unseen")

    player = DummyPlayer(
        vision=DummyVision(
            states={
                "visible": VisionTileState.VISIBLE,
                "fogged": VisionTileState.FOGGED,
                "unseen": VisionTileState.UNSEEN,
            },
            visible_tags={"visible"},
            explored_tags={"visible", "fogged"},
        )
    )

    tile_grid = DummyTileGrid()
    tile_overlay = DummyTileOverlay()
    label_overlay = DummyLabelOverlay()
    visible_unit = DummyUnit(visible_tile)
    hidden_unit = DummyUnit(fogged_tile)

    controller.apply(
        player,
        [visible_tile, fogged_tile, unseen_tile],
        [visible_unit, hidden_unit],
        tile_grid=tile_grid,
        tile_overlay=tile_overlay,
        label_overlay=label_overlay,
    )

    assert visible_tile.renderer.states[-1] is VisionTileState.VISIBLE
    assert fogged_tile.renderer.states[-1] is VisionTileState.FOGGED
    assert unseen_tile.renderer.states[-1] is VisionTileState.UNSEEN
    assert visible_tile.renderer.fog_ceilings[-1] == 3.6

    assert "visible" in tile_grid.shown
    assert sorted(tile_grid.hidden) == ["fogged", "unseen"]
    assert tile_grid.tinted == {}
    assert sorted(tile_grid.cleared) == ["fogged", "unseen", "visible"]
    assert tile_grid.collect_calls == 1

    assert tile_overlay.shown == ["visible"]
    assert tile_overlay.hidden == ["fogged", "unseen"]

    assert visible_unit.visible is True
    assert hidden_unit.visible is False
    assert label_overlay.root.hidden is True


def test_fog_controller_restores_labels_after_full_exploration() -> None:
    controller = FogOfWarController()
    first_tile = DummyTile("first")
    second_tile = DummyTile("second")
    label_overlay = DummyLabelOverlay()

    player = DummyPlayer(
        vision=DummyVision(
            states={
                "first": VisionTileState.VISIBLE,
                "second": VisionTileState.FOGGED,
            },
            visible_tags={"first"},
            explored_tags={"first", "second"},
        )
    )

    controller.apply(
        player,
        [first_tile, second_tile],
        [],
        tile_grid=DummyTileGrid(),
        tile_overlay=DummyTileOverlay(),
        label_overlay=label_overlay,
    )

    assert label_overlay.root.shown is True


def test_fog_controller_can_limit_tile_updates_to_changed_tags() -> None:
    controller = FogOfWarController()
    first_tile = DummyTile("first")
    second_tile = DummyTile("second")
    tile_grid = DummyTileGrid()
    tile_overlay = DummyTileOverlay()

    player = DummyPlayer(
        vision=DummyVision(
            states={
                "first": VisionTileState.VISIBLE,
                "second": VisionTileState.UNSEEN,
            },
            visible_tags={"first"},
            explored_tags={"first"},
        )
    )

    controller.apply(
        player,
        [first_tile, second_tile],
        [],
        tile_grid=tile_grid,
        tile_overlay=tile_overlay,
    )

    tile_grid.hidden.clear()
    tile_grid.shown.clear()
    tile_grid.cleared.clear()
    tile_overlay.hidden.clear()
    tile_overlay.shown.clear()
    first_tile.renderer.states.clear()
    second_tile.renderer.states.clear()

    controller.apply(
        player,
        [first_tile, second_tile],
        [],
        tile_grid=tile_grid,
        tile_overlay=tile_overlay,
        changed_tile_tags={"second"},
    )

    assert first_tile.renderer.states == []
    assert second_tile.renderer.states[-1] is VisionTileState.UNSEEN
    assert tile_grid.hidden == ["second"]
    assert tile_overlay.hidden == ["second"]


def test_fog_controller_full_syncs_unsynced_player_even_with_changed_tiles() -> None:
    controller = FogOfWarController()
    visible_tile = DummyTile("visible")
    unseen_tile = DummyTile("unseen")
    tile_grid = DummyTileGrid()
    tile_overlay = DummyTileOverlay()

    player = DummyPlayer(
        vision=DummyVision(
            states={
                "visible": VisionTileState.VISIBLE,
                "unseen": VisionTileState.UNSEEN,
            },
            visible_tags={"visible"},
            explored_tags={"visible"},
        )
    )

    controller.apply(
        player,
        [visible_tile, unseen_tile],
        [],
        tile_grid=tile_grid,
        tile_overlay=tile_overlay,
        changed_tile_tags={"visible"},
    )

    assert unseen_tile.renderer.states[-1] is VisionTileState.UNSEEN
    assert tile_grid.hidden == ["unseen"]
    assert tile_overlay.hidden == ["unseen"]
