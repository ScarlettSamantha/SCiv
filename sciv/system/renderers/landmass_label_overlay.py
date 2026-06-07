import math
from collections import defaultdict
from collections.abc import Collection, Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, cast

from helpers.cache import Cache
from panda3d.core import BitMask32, NodePath, TextNode, TransparencyAttrib
from system.zoom_visibility import ZoomVisibilityController, ZoomVisibilityRule

if TYPE_CHECKING:
    from gameplay.tile import Tile


DISPLAY_LANDMASS_TYPES: frozenset[str] = frozenset({"Continent", "Large Island", "Peninsula"})
DEFAULT_MIN_LANDMASS_SIZE: int = 18
DEFAULT_MIN_TERRITORY_SIZE: int = 10
LANDMASS_LABEL_Z_OFFSET: float = 2.3
TERRITORY_LABEL_Z_OFFSET: float = 2.05
LANDMASS_ZOOM_RULE = ZoomVisibilityRule(min_zoom=30.0, fade_in=12.0)
TERRITORY_ZOOM_RULE = ZoomVisibilityRule(min_zoom=10.0, max_zoom=42.0, fade_in=10.0, fade_out=18.0)


class LandmassTileLike(Protocol):
    x: int
    y: int
    pos_x: float
    pos_y: float
    pos_z: float


@dataclass(slots=True, frozen=True)
class LandmassLabelSpec:
    name: str
    display_text: str
    anchor: tuple[float, float, float]
    scale: float
    alpha: float
    size: int


def spread_label_text(name: str) -> str:
    words = [segment.strip().upper() for segment in str(name).split() if segment.strip()]
    if not words:
        return ""

    return "   ".join(" ".join(list(word)) for word in words)


def territory_label_text(name: str) -> str:
    words = [segment.strip().upper() for segment in str(name).split() if segment.strip()]
    return " ".join(words)


def _landmass_size(tiles: Collection[LandmassTileLike]) -> int:
    size_values = [int(getattr(tile, "landmass_size", 0) or 0) for tile in tiles]
    return max(max(size_values, default=0), len(tiles))


def _territory_size(tiles: Collection[LandmassTileLike]) -> int:
    size_values = [int(getattr(tile, "territory_size", 0) or 0) for tile in tiles]
    return max(max(size_values, default=0), len(tiles))


def _label_scale(size: int) -> float:
    return max(0.8, min(1.45, 0.72 + math.sqrt(float(size)) * 0.055))


def _label_alpha(size: int) -> float:
    return max(0.4, min(0.4, 0.4 + math.sqrt(float(size)) * 0.054))


def _territory_label_scale(size: int) -> float:
    return max(0.86, min(1.34, 0.74 + math.sqrt(float(size)) * 0.055))


def _territory_label_alpha(size: int) -> float:
    return max(0.5, min(0.82, 0.4 + math.sqrt(float(size)) * 0.054))


def _choose_anchor_tile(tiles: Collection[LandmassTileLike]) -> LandmassTileLike:
    centroid_x = sum(float(tile.pos_x) for tile in tiles) / max(1, len(tiles))
    centroid_y = sum(float(tile.pos_y) for tile in tiles) / max(1, len(tiles))

    return min(
        tiles,
        key=lambda tile: ((float(tile.pos_x) - centroid_x) ** 2) + ((float(tile.pos_y) - centroid_y) ** 2),
    )


def _choose_territory_anchor_tile(tiles: Collection[LandmassTileLike]) -> LandmassTileLike:
    preferred_anchor = next((tile for tile in tiles if bool(getattr(tile, "territory_is_anchor", False))), None)
    if preferred_anchor is not None:
        return preferred_anchor

    return _choose_anchor_tile(tiles)


def build_landmass_label_specs(
    tiles: Iterable[LandmassTileLike],
    *,
    allowed_types: Collection[str] = DISPLAY_LANDMASS_TYPES,
    min_landmass_size: int = DEFAULT_MIN_LANDMASS_SIZE,
) -> list[LandmassLabelSpec]:
    grouped_tiles: dict[str, list[LandmassTileLike]] = defaultdict(list)

    for tile in tiles:
        landmass_name = getattr(tile, "landmass_name", None)
        landmass_type = getattr(tile, "landmass_type", None)

        if not landmass_name or not isinstance(landmass_name, str):
            continue

        if allowed_types and landmass_type not in allowed_types:
            continue

        grouped_tiles[landmass_name].append(tile)

    specs: list[LandmassLabelSpec] = []
    for name, group in grouped_tiles.items():
        size = _landmass_size(group)
        if size < min_landmass_size:
            continue

        anchor_tile = _choose_anchor_tile(group)
        specs.append(
            LandmassLabelSpec(
                name=name,
                display_text=spread_label_text(name),
                anchor=(
                    float(anchor_tile.pos_x),
                    float(anchor_tile.pos_y),
                    float(anchor_tile.pos_z) + LANDMASS_LABEL_Z_OFFSET,
                ),
                scale=_label_scale(size),
                alpha=_label_alpha(size),
                size=size,
            )
        )

    specs.sort(key=lambda spec: spec.size, reverse=True)
    return specs


def build_territory_label_specs(
    tiles: Iterable[LandmassTileLike],
    *,
    min_territory_size: int = DEFAULT_MIN_TERRITORY_SIZE,
) -> list[LandmassLabelSpec]:
    grouped_tiles: dict[int, list[LandmassTileLike]] = defaultdict(list)
    names_by_id: dict[int, str] = {}

    for tile in tiles:
        territory_id = getattr(tile, "territory_id", None)
        territory_name = getattr(tile, "territory_name", None)

        if not isinstance(territory_id, int) or territory_id <= 0:
            continue

        if not territory_name or not isinstance(territory_name, str):
            continue

        grouped_tiles[territory_id].append(tile)
        names_by_id.setdefault(territory_id, territory_name)

    specs: list[LandmassLabelSpec] = []
    for territory_id, group in grouped_tiles.items():
        territory_size = _territory_size(group)
        if territory_size < min_territory_size:
            continue

        anchor_tile = _choose_territory_anchor_tile(group)
        territory_name = names_by_id[territory_id]
        specs.append(
            LandmassLabelSpec(
                name=territory_name,
                display_text=territory_label_text(territory_name),
                anchor=(
                    float(anchor_tile.pos_x),
                    float(anchor_tile.pos_y),
                    float(anchor_tile.pos_z) + TERRITORY_LABEL_Z_OFFSET,
                ),
                scale=_territory_label_scale(territory_size),
                alpha=_territory_label_alpha(territory_size),
                size=territory_size,
            )
        )

    specs.sort(key=lambda spec: spec.size, reverse=True)
    return specs


class LandmassLabelOverlay:
    _instance: "LandmassLabelOverlay | None" = None

    @classmethod
    def get(cls) -> "LandmassLabelOverlay":
        instance = cls._instance
        if instance is None or instance.root.is_empty():
            instance = cls()
            cls._instance = instance
        return instance

    def __init__(self) -> None:
        from managers.assets import AssetManager

        self.base = Cache.get_showbase_instance()
        self.root: NodePath = self.base.render.attachNewNode("landmass_label_overlay")
        self.root.setTransparency(TransparencyAttrib.M_alpha)
        self.root.setDepthWrite(False)
        self.root.setDepthTest(False)
        self.root.setBin("fixed", 88)
        self.root.setCollideMask(BitMask32.allOff())
        self.root.setLightOff()

        self._territory_root: NodePath = self.root.attachNewNode("territory_labels")
        self._landmass_root: NodePath = self.root.attachNewNode("landmass_labels")

        self._font = AssetManager.load_font("assets/fonts/Washington.ttf")
        zoom_controller = ZoomVisibilityController.get()
        self._territory_zoom_binding_id = zoom_controller.register_node(self._territory_root, TERRITORY_ZOOM_RULE)
        self._landmass_zoom_binding_id = zoom_controller.register_node(self._landmass_root, LANDMASS_ZOOM_RULE)

        self.root.show()
        self._territory_root.hide()
        self._landmass_root.hide()

    def clear(self) -> None:
        if self.root.is_empty():
            return

        for node in (self._territory_root, self._landmass_root):
            for child in node.getChildren():
                child.removeNode()
            node.hide()
            node.setColorScale(1.0, 1.0, 1.0, 1.0)

    def destroy(self) -> None:
        zoom_controller = ZoomVisibilityController.get()
        zoom_controller.unregister(self._territory_zoom_binding_id)
        zoom_controller.unregister(self._landmass_zoom_binding_id)
        self.clear()
        self.root.removeNode()

    def rebuild(self, tiles: Iterable["Tile"]) -> None:
        self.clear()
        tile_iterable = cast(Iterable[LandmassTileLike], tiles)
        cached_tiles = list(tile_iterable)

        territory_specs = build_territory_label_specs(cached_tiles)
        landmass_specs = build_landmass_label_specs(cached_tiles)

        for index, spec in enumerate(territory_specs):
            self._add_label(
                self._territory_root,
                index,
                spec,
                text_scale=0.46,
                bin_order=89,
                text_color=(1.0, 0.97, 0.84),
                shadow_alpha_cap=0.58,
                shadow_alpha_multiplier=1.35,
                shadow_offset=0.04,
            )

        for index, spec in enumerate(landmass_specs):
            self._add_label(
                self._landmass_root,
                index,
                spec,
                text_scale=0.55,
                bin_order=88,
                text_color=(0.97, 0.93, 0.78),
                shadow_alpha_cap=0.22,
                shadow_alpha_multiplier=0.9,
                shadow_offset=0.025,
            )

        zoom_controller = ZoomVisibilityController.get()
        zoom_controller.refresh(self._territory_zoom_binding_id)
        zoom_controller.refresh(self._landmass_zoom_binding_id)

    def _add_label(
        self,
        parent: NodePath,
        index: int,
        spec: LandmassLabelSpec,
        *,
        text_scale: float,
        bin_order: int,
        text_color: tuple[float, float, float],
        shadow_alpha_cap: float,
        shadow_alpha_multiplier: float,
        shadow_offset: float,
    ) -> None:
        text_node = TextNode(f"landmass_label_{index}")
        text_node.setFont(self._font)
        text_node.setAlign(TextNode.ACenter)
        text_node.setText(spec.display_text)
        text_node.setTextScale(text_scale)
        text_node.setTextColor(text_color[0], text_color[1], text_color[2], spec.alpha)
        text_node.setShadow(shadow_offset, shadow_offset)
        text_node.setShadowColor(
            0.02,
            0.02,
            0.03,
            min(shadow_alpha_cap, spec.alpha * shadow_alpha_multiplier),
        )

        node = parent.attachNewNode(text_node)
        node.setPos(*spec.anchor)
        node.setScale(spec.scale)
        node.setBillboardAxis()
        node.setTransparency(TransparencyAttrib.M_alpha)
        node.setDepthWrite(False)
        node.setDepthTest(False)
        node.setBin("fixed", bin_order)
        node.setCollideMask(BitMask32.allOff())
        node.setLightOff()
