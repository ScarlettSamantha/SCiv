import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional, Set, Tuple, Type

from gameplay.terrain._base_terrain import BaseTerrain
from helpers.cache import Cache
from panda3d.core import (
    CardMaker,
    LPoint3f,
    NodePath,
    PandaNode,
    RigidBodyCombiner,
    TransparencyAttrib,
)

from gameplay.repositories.terrain import TerrainRepository
from helpers.paths import PathsHelper

if TYPE_CHECKING:
    from managers.entity import Tile


@dataclass(frozen=True)
class TerrainModelSpec:
    key: str
    path: str
    scale: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    hpr: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    z_offset: float = -0.4


class TileModelGrid:
    def __init__(
        self,
        tiles: List["Tile"],
        *,
        radius: float = 1.0,
        cols: Optional[int] = None,
        rows: Optional[int] = None,
        default_model_path: str = "assets/models/terrain/default_hex.bam",
    ) -> None:
        self.radius = float(radius)
        self.tiles: List["Tile"] = list(tiles)
        self.cols = cols or 10
        self.rows = rows or 10
        self.base = Cache.get_showbase_instance()
        TerrainRepository.load(str(PathsHelper.get_terrain_dir()))
        self.terrain_available: Set[Type["BaseTerrain"]] = TerrainRepository.get_all()

        self.root_np: NodePath = NodePath(PandaNode("tile_model_grid"))
        self._attached = False

        self._rbc_nodes: Dict[str, NodePath] = {}
        self._rbc_controls: Dict[str, RigidBodyCombiner] = {}
        self._prototypes: Dict[str, NodePath] = {}
        self._tile_to_np: Dict[Tuple[int, int], NodePath] = {}

        self._default_path = default_model_path

        self.rebuild(self.tiles)

    def attach_to_render(self, parent: Optional[NodePath] = None) -> None:
        if parent is None:
            parent = getattr(self.base, "render", None)
            if parent is None:
                try:
                    parent = render  # type: ignore[name-defined]
                except NameError:
                    parent = None

        if parent is None:
            self._attached = False
            return

        if self._attached and (not self.root_np.is_empty()) and self.root_np.get_parent() == parent:
            return

        self.root_np.reparent_to(parent)  # type: ignore
        self.root_np.flatten_light()
        self._attached = True

    def dispose(self) -> None:
        for np in list(self._tile_to_np.values()):
            if not np.is_empty():
                np.remove_node()
        self._tile_to_np.clear()

        for np in self._rbc_nodes.values():
            if not np.is_empty():
                np.remove_node()
        self._rbc_nodes.clear()
        self._rbc_controls.clear()

        for proto in self._prototypes.values():
            if not proto.is_empty():
                proto.remove_node()
        self._prototypes.clear()

        if not self.root_np.is_empty():
            self.root_np.remove_node()

    def rebuild(self, tiles: Iterable["Tile"]) -> None:
        self._clear_instances_only()
        self.tiles = list(tiles)
        for tile in self.tiles:
            self._ensure_instance_for_tile(tile)
        self.collect()

    def update_tile(self, tile: "Tile") -> None:
        key = (int(tile.x), int(tile.y))
        old_np = self._tile_to_np.pop(key, None)
        if old_np and not old_np.is_empty():
            old_np.remove_node()
        self._ensure_instance_for_tile(tile)
        tile.calculate()
        tile.renderer.render()
        self.collect()

    def set_tile_tint(
        self, tile_or_index: "Tile | Tuple[int,int] | int", rgba: Tuple[float, float, float, float]
    ) -> None:
        np = self._instance_np_for(tile_or_index)
        if np:
            np.set_color_scale(*rgba)

    def clear_tile_tint(self, tile_or_index: "Tile | Tuple[int,int] | int") -> None:
        np = self._instance_np_for(tile_or_index)
        if np:
            np.clear_color_scale()

    def collect(self) -> None:
        for ctrl in self._rbc_controls.values():
            ctrl.collect()

    @staticmethod
    def _hex_spacing(radius: float) -> Tuple[float, float]:
        return 1.5 * radius, math.sqrt(3.0) * radius

    def _world_xy_for(self, col: int, row: int) -> Tuple[float, float]:
        dx, dy = self._hex_spacing(self.radius)
        x = col * dx
        y = row * dy + (dy * 0.5 if (col % 2) else 0.0)
        return x, y

    def _render_xy_for_tile(self, tile: "Tile") -> Tuple[float, float]:
        return self._world_xy_for(int(tile.x), int(tile.y))

    def _extract_spec_for_tile(self, tile: "Tile") -> TerrainModelSpec:
        key = tile.get_terrain().get_key()  # type: ignore[attr-defined]
        path = tile.get_model()  # type: ignore[attr-defined]
        terr_obj = tile.get_terrain()

        return TerrainModelSpec(
            key=str(key),
            path=str(path),
            scale=terr_obj.model_scale,  # type: ignore[arg-type]
            hpr=terr_obj.model_hpr,  # type: ignore[arg-type]
            z_offset=terr_obj.model_pos_z_offset,
        )

    def _prototype_for(self, path: str) -> NodePath:
        np = self._prototypes.get(path)
        if np and not np.is_empty():
            return np

        model: Optional[NodePath] = None
        model = self.base.loader.load_model(path)

        if model is None or model.is_empty():
            cm = CardMaker(f"missing:{path}")
            cm.set_frame(-0.45, 0.45, -0.45, 0.45)
            card = NodePath(cm.generate())
            card.set_transparency(TransparencyAttrib.MAlpha)
            card.set_color(1.0, 0.2, 0.2, 0.8)
            card.set_two_sided(True)
            self._prototypes[path] = card
            return card

        self._prototypes[path] = model
        return model

    def _rbc_for_key(self, key: str) -> Tuple[NodePath, RigidBodyCombiner]:
        rbc_np = self._rbc_nodes.get(key)
        if rbc_np and not rbc_np.is_empty():
            return rbc_np, self._rbc_controls[key]
        ctrl = RigidBodyCombiner(f"rbc_{key}")
        rbc_np = NodePath(ctrl)
        rbc_np.reparent_to(self.root_np)
        self._rbc_nodes[key] = rbc_np
        self._rbc_controls[key] = ctrl
        return rbc_np, ctrl

    def _ensure_instance_for_tile(self, tile: "Tile") -> None:
        spec = self._extract_spec_for_tile(tile)
        proto = self._prototype_for(spec.path)
        rbc_np, _ = self._rbc_for_key(spec.key)

        inst = proto.copy_to(rbc_np)
        terrain = tile.get_terrain()

        rx, ry = self._render_xy_for_tile(tile)
        z = float(tile.calculate_z_pos_on_altitude()[2])
        inst.set_pos(LPoint3f(rx, ry, z + terrain.model_pos_z_offset))  # type: ignore[attr-defined]
        inst.set_hpr(spec.hpr[0] + 30, spec.hpr[1], spec.hpr[2])
        inst.set_scale(tile.get_terrain().model_scale)

        self._tile_to_np[(int(tile.x), int(tile.y))] = inst

    def _instance_np_for(self, tile_or_index: "Tile | Tuple[int,int] | int") -> Optional[NodePath]:
        if isinstance(tile_or_index, tuple):
            return self._tile_to_np.get((int(tile_or_index[0]), int(tile_or_index[1])))
        if isinstance(tile_or_index, int):
            try:
                t = self.tiles[tile_or_index]
            except IndexError:
                return None
            return self._tile_to_np.get((int(t.x), int(t.y)))
        return self._tile_to_np.get((int(tile_or_index.x), int(tile_or_index.y)))

    def _clear_instances_only(self) -> None:
        for np in list(self._tile_to_np.values()):
            if not np.is_empty():
                np.remove_node()
        self._tile_to_np.clear()
