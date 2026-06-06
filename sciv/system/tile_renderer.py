from typing import Any, Dict, List, Optional, Set, Tuple, Union

from gameplay.resource import BaseResource
from helpers.cache import Cache
from panda3d.core import (
    BitMask32,
    ColorBlendAttrib,
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexArrayFormat,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    NodePath,
    OmniBoundingVolume,
    SamplerState,
    Texture,
    TransparencyAttrib,
)
from system.asset_archive import P3DAssetArchive
from system.atlas import AtlasGenerator

T_TileRef = Any  # type: ignore


class TileRendererSystem:
    _instance: Optional["TileRendererSystem"] = None

    ICON_SLOTS: int = 7
    TILE_SCALE: float = 1.65
    CENTER_OFF_X: float = -1
    CENTER_OFF_Y: float = -1

    @classmethod
    def get(cls) -> "TileRendererSystem":
        if cls._instance is None:
            cls._instance = TileRendererSystem()
        return cls._instance

    def __init__(self) -> None:
        self.base = Cache.get_showbase_instance()
        self.icon_atlas: AtlasGenerator = Cache.get_icon_atlas()
        self.node: NodePath = NodePath("tile_renderer_system")
        self.node.reparentTo(self.base.render)
        self.node.setTransparency(TransparencyAttrib.M_alpha)
        self.node.setAttrib(ColorBlendAttrib.makeOff())
        self.node.setBin("fixed", 85)
        self.node.setDepthTest(False)
        self.node.setDepthWrite(False)
        self.node.setScale(1.0)
        self.node.setCollideMask(BitMask32.allOff())

        self._tiles: List[Optional[T_TileRef]] = []
        self._tile_index: Dict[str, int] = {}
        self._hidden_tile_tags: Set[str] = set()
        self._geom_node: Optional[GeomNode] = None
        self._geom_np: Optional[NodePath] = None
        self._vdata: Optional[GeomVertexData] = None
        self._capacity: int = 0
        self._bulk: bool = False

        self.assets: P3DAssetArchive = Cache.get_asset_archive()

        self._wps: Optional[GeomVertexWriter] = None
        self._wuv: List[GeomVertexWriter] = []

        self._atlas_tex: Texture = self.icon_atlas.get_panda3d_texture()
        self._atlas_tex.setWrapU(Texture.WM_clamp)
        self._atlas_tex.setWrapV(Texture.WM_clamp)
        self._atlas_tex.setFormat(Texture.F_srgb_alpha)
        self._atlas_tex.setMinfilter(SamplerState.FT_linear)
        self._atlas_tex.setMagfilter(SamplerState.FT_linear)

        self._atlas_w, self._atlas_h = self.icon_atlas.atlas_image.size

        self._half_w: float = self.TILE_SCALE * 0.5
        self._half_h: float = self._half_w * 0.8660254037844386

        self._uv_cache: Dict[str, Tuple[float, float, float, float]] = {}

        self._setup_shader()

    def _setup_shader(self) -> None:
        vs = "assets/shaders/tile_icons_instanced.vert.glsl"
        fs = "assets/shaders/tile_icons_instanced.frag.glsl"
        self.node.setShader(self.assets.get_shader(str(fs), str(vs)))
        self.node.set_shader_input("icon_atlas", self._atlas_tex)  # type: ignore
        self.node.set_shader_input("u_aniso", (1.0, 0.8660254037844386))  # type: ignore
        self.node.set_shader_input("u_ring_radius", 0.90 * self._half_w)  # type: ignore
        self.node.set_shader_input("u_icon_half", 0.22 * self._half_w)  # type: ignore

    def begin_bulk(self) -> None:
        self._bulk = True

    def end_bulk(self) -> None:
        self._bulk = False
        self._ensure_capacity(len(self._tiles))
        for t in self._tiles:
            if t is not None:
                self.sync_tile(t)

    def register_tiles(self, tiles: List[T_TileRef]) -> None:
        for t in tiles:
            tag = t.tag
            if tag not in self._tile_index:
                self._tile_index[tag] = len(self._tiles)
                self._tiles.append(t)
        self._ensure_capacity(len(self._tiles))
        for t in tiles:
            self.sync_tile(t)

    def register_tile(self, tile: T_TileRef) -> None:
        tag = tile.tag
        if tag in self._tile_index:
            self.sync_tile(tile)
            return
        self._tile_index[tag] = len(self._tiles)
        self._tiles.append(tile)
        if not self._bulk:
            self._ensure_capacity(len(self._tiles))
            self.sync_tile(tile)

    def remove_tile(self, tile: T_TileRef) -> None:
        tag = tile.tag
        if tag not in self._tile_index:
            return

        idx = self._tile_index.pop(tag)
        self._hidden_tile_tags.discard(tag)
        self._tiles[idx] = None
        self._write_instance_clear(idx)

    def hide_tile(self, tile: T_TileRef) -> None:
        tag = tile.tag
        self._hidden_tile_tags.add(tag)

        idx = self._tile_index.get(tag)
        if idx is None:
            return

        self._write_instance_clear(idx)

    def show_tile(self, tile: T_TileRef) -> None:
        tag = tile.tag
        self._hidden_tile_tags.discard(tag)

        idx = self._tile_index.get(tag)
        if idx is None:
            self.register_tile(tile)
            return

        self._write_instance_row(idx, tile)

    def sync_tile(self, tile: T_TileRef) -> None:
        if self._vdata is None:
            self.register_tile(tile)
            return

        idx = self._tile_index.get(tile.tag)
        if idx is None:
            self.register_tile(tile)
            return

        if tile.tag in self._hidden_tile_tags:
            self._write_instance_clear(idx)
            return

        self._write_instance_row(idx, tile)

    def _next_capacity(self, target: int) -> int:
        cap = self._capacity if self._capacity > 0 else 4
        while cap < target:
            cap *= 2
        return cap

    def _ensure_capacity(self, target: int) -> None:
        if target <= 0:
            return
        if self._vdata is None or target > self._capacity:
            cap = self._next_capacity(target)
            self._build_or_resize(cap)
        if self._geom_np is not None:
            self._geom_np.set_instance_count(target)

    def _init_writers(self) -> None:
        if self._vdata is None:
            return
        self._wps = GeomVertexWriter(self._vdata, "i_pos_scale")
        self._wuv = [GeomVertexWriter(self._vdata, f"i_uv{s}") for s in range(self.ICON_SLOTS)]

    def _build_or_resize(self, instances: int) -> None:
        if self._vdata is not None and self._geom_node is not None and self._geom_np is not None:
            self._vdata.modifyArray(1).setNumRows(instances)
            self._capacity = instances
            self._init_writers()
            return

        vfmt0 = GeomVertexArrayFormat()
        vfmt0.addColumn("vertex", 3, Geom.NTFloat32, Geom.CPoint)
        vfmt0.addColumn("texcoord", 2, Geom.NTFloat32, Geom.CTexcoord)

        vfmt1 = GeomVertexArrayFormat()
        vfmt1.addColumn("i_pos_scale", 4, Geom.NTFloat32, Geom.COther)
        vfmt1.addColumn("i_uv0", 4, Geom.NTFloat32, Geom.COther)
        vfmt1.addColumn("i_uv1", 4, Geom.NTFloat32, Geom.COther)
        vfmt1.addColumn("i_uv2", 4, Geom.NTFloat32, Geom.COther)
        vfmt1.addColumn("i_uv3", 4, Geom.NTFloat32, Geom.COther)
        vfmt1.addColumn("i_uv4", 4, Geom.NTFloat32, Geom.COther)
        vfmt1.addColumn("i_uv5", 4, Geom.NTFloat32, Geom.COther)
        vfmt1.addColumn("i_uv6", 4, Geom.NTFloat32, Geom.COther)
        vfmt1.set_divisor(1)

        vfmt = GeomVertexFormat()
        vfmt.addArray(vfmt0)
        vfmt.addArray(vfmt1)
        vfmt = GeomVertexFormat.registerFormat(vfmt)

        vdata = GeomVertexData("tile_icons_vdata", vfmt, Geom.UH_dynamic)
        vdata.setNumRows(4)

        wv = GeomVertexWriter(vdata, "vertex")
        wt = GeomVertexWriter(vdata, "texcoord")

        wv.addData3f(-1.0, 0.0, -1.0)
        wt.addData2f(0.0, 0.0)
        wv.addData3f(1.0, 0.0, -1.0)
        wt.addData2f(1.0, 0.0)
        wv.addData3f(1.0, 0.0, 1.0)
        wt.addData2f(1.0, 1.0)
        wv.addData3f(-1.0, 0.0, 1.0)
        wt.addData2f(0.0, 1.0)

        tris = GeomTriangles(Geom.UH_static)
        tris.addVertices(0, 1, 2)
        tris.addVertices(0, 2, 3)

        geom = Geom(vdata)
        geom.addPrimitive(tris)

        vdata.modifyArray(1).setNumRows(instances)

        self._vdata = vdata
        self._geom_node = GeomNode("tile_icons_node")
        self._geom_node.removeAllGeoms()
        self._geom_node.addGeom(geom)

        self.node.getChildren().detach()

        self._geom_np = self.node.attachNewNode(self._geom_node)
        self._geom_np.set_instance_count(instances)
        self._geom_np.node().setBounds(OmniBoundingVolume())
        self._geom_np.node().setFinal(True)
        self._geom_np.setCollideMask(BitMask32.allOff())

        self._capacity = instances
        self._init_writers()

    def _write_instance_clear(self, idx: int) -> None:
        if self._vdata is None:
            return
        if self._wps is None or not self._wuv:
            self._init_writers()
        if self._wps is None or not self._wuv:
            return
        for w in self._wuv:
            w.setRow(idx)
            w.setData4f(0.0, 0.0, 0.0, 0.0)
        self._wps.setRow(idx)
        self._wps.setData4f(0.0, 0.0, 0.0, 0.0)

    def _get_uv_rect(self, path: str) -> Tuple[float, float, float, float]:
        if not path:
            return 0.0, 0.0, 0.0, 0.0
        cached = self._uv_cache.get(path)
        if cached is not None:
            return cached
        pos = self.icon_atlas.get_position_for_virtual_path(path)
        size = self.icon_atlas.get_dimensions_for_virtual_path(path)

        if not pos or not size:
            rect = (0.0, 0.0, 0.0, 0.0)
            self._uv_cache[path] = rect
            return rect

        x, y = pos
        w, h = size

        u0 = float(x) / float(self._atlas_w)
        v0 = 1.0 - float(y + h) / float(self._atlas_h)
        u1 = float(x + w) / float(self._atlas_w)
        v1 = 1.0 - float(y) / float(self._atlas_h)

        rect = (u0, v0, u1, v1)
        self._uv_cache[path] = rect
        return rect

    def _write_instance_row(self, idx: int, tile: T_TileRef) -> None:
        if self._vdata is None:
            return
        if self._wps is None or not self._wuv:
            self._init_writers()
        if self._wps is None or not self._wuv:
            return

        px, py, pz = tile.get_cords()

        cx = px + self._half_w + self._half_w * self.CENTER_OFF_X
        cy = py + self._half_h + self._half_h * self.CENTER_OFF_Y

        self._wps.setRow(idx)
        self._wps.setData4f(float(cx), float(cy), float(pz + 0.01), self._half_w)

        slots: List[Union[str, BaseResource, None]]
        tile.calculate()
        base_yields = tile.get_tile_yield()

        if tile.city:
            slots = [tile.city.get_population_icon()]
        else:
            res_list: List[BaseResource] = list(tile.resources.flatten().values())
            main_res: Optional[BaseResource] = res_list[0] if res_list else None
            slots = [main_res]

        slots += base_yields.export_basic()
        slots = slots[: self.ICON_SLOTS] + [None] * max(0, self.ICON_SLOTS - len(slots))

        def _norm(p: str) -> str:
            return p.replace("\\", "/").lstrip("/")

        for idx_slot, entry in enumerate(slots):
            if not entry or (isinstance(entry, BaseResource) and getattr(entry, "value", 0.0) == 0.0):
                u0 = 0.0
                v0 = 0.0
                u1 = 0.0
                v1 = 0.0
            else:
                if idx_slot != 0 and isinstance(entry, BaseResource) and getattr(entry, "value", 0.0) > 0.0:
                    entry = entry.get_numeric_icon() if hasattr(entry, "get_numeric_icon") else entry.icon

                if isinstance(entry, BaseResource):
                    path = _norm(entry.icon) if hasattr(entry, "icon") else ""
                else:
                    path = _norm(entry)

                if not path:
                    u0 = 0.0
                    v0 = 0.0
                    u1 = 0.0
                    v1 = 0.0
                else:
                    u0, v0, u1, v1 = self._get_uv_rect(path)

            w = self._wuv[idx_slot]
            w.setRow(idx)
            w.setData4f(u0, v0, u1, v1)

    def set_all_disabled(self, disabled: bool) -> None:
        if self._vdata is None:
            return
        if disabled:
            for i, t in enumerate(self._tiles):
                if t is None:
                    continue
                self._write_instance_clear(i)
        else:
            for t in self._tiles:
                if t is None:
                    continue
                self.sync_tile(t)

    def atlas_size(self) -> Tuple[int, int]:
        return self.icon_atlas.atlas_image.size

    def dump(self) -> Dict[str, Any]:
        return {"tiles": len([t for t in self._tiles if t is not None])}
