from typing import Any, Dict, List, Optional, Tuple, Union

from gameplay.resource import BaseResource
from helpers.cache import Cache
from panda3d.core import (
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
    Shader,
    Texture,
    TransparencyAttrib,
)
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

        self._tiles: List[Optional[T_TileRef]] = []
        self._tile_index: Dict[str, int] = {}
        self._geom_node: Optional[GeomNode] = None
        self._geom_np: Optional[NodePath] = None
        self._vdata: Optional[GeomVertexData] = None

        self._atlas_tex: Texture = self.icon_atlas.get_panda3d_texture()
        self._atlas_tex.setWrapU(Texture.WM_clamp)
        self._atlas_tex.setWrapV(Texture.WM_clamp)
        self._atlas_tex.setFormat(Texture.F_srgb_alpha)
        self._atlas_tex.setMinfilter(SamplerState.FT_linear)
        self._atlas_tex.setMagfilter(SamplerState.FT_linear)

        self._setup_shader()

    def _setup_shader(self) -> None:
        vs = self.base.base_path / "../assets/shaders/tile_icons_instanced.vert.glsl"
        fs = self.base.base_path / "../assets/shaders/tile_icons_instanced.frag.glsl"
        self.node.setShader(Shader.load(Shader.SL_GLSL, str(vs), str(fs)))
        self.node.set_shader_input("icon_atlas", self._atlas_tex)  # type: ignore
        self.node.set_shader_input("u_aniso", (1.0, 0.8660254037844386))  # type: ignore
        half_w = self.TILE_SCALE * 0.5
        self.node.set_shader_input("u_ring_radius", 0.90 * half_w)  # type: ignore
        self.node.set_shader_input("u_icon_half", 0.22 * half_w)  # type: ignore

    def register_tiles(self, tiles: List[T_TileRef]) -> None:
        for t in tiles:
            tag = t.tag
            if tag not in self._tile_index:
                self._tile_index[tag] = len(self._tiles)
                self._tiles.append(t)
        self._build_or_resize(len(self._tiles))
        for t in tiles:
            self.sync_tile(t)

    def register_tile(self, tile: T_TileRef) -> None:
        tag = tile.tag
        if tag in self._tile_index:
            self.sync_tile(tile)
            return
        self._tile_index[tag] = len(self._tiles)
        self._tiles.append(tile)
        self._build_or_resize(len(self._tiles))
        self.sync_tile(tile)

    def remove_tile(self, tile: T_TileRef) -> None:
        tag = tile.tag
        if tag not in self._tile_index:
            return
        idx = self._tile_index.pop(tag)
        self._tiles[idx] = None
        self._write_instance_clear(idx)

    def sync_tile(self, tile: T_TileRef) -> None:
        if self._vdata is None:
            self.register_tile(tile)
            return
        idx = self._tile_index.get(tile.tag)
        if idx is None:
            self.register_tile(tile)
            return
        self._write_instance_row(idx, tile)

    def _build_or_resize(self, instances: int) -> None:
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

    def _write_instance_clear(self, idx: int) -> None:
        if self._vdata is None:
            return
        for name in ("i_uv0", "i_uv1", "i_uv2", "i_uv3", "i_uv4", "i_uv5", "i_uv6"):
            w = GeomVertexWriter(self._vdata, name)
            w.setRow(idx)
            w.setData4f(0.0, 0.0, 0.0, 0.0)
        wps = GeomVertexWriter(self._vdata, "i_pos_scale")
        wps.setRow(idx)
        wps.setData4f(0.0, 0.0, 0.0, 0.0)

    def _write_instance_row(self, idx: int, tile: T_TileRef) -> None:
        if self._vdata is None:
            return

        px, py, pz = tile.get_cords()
        half_w = self.TILE_SCALE * 0.5
        half_h = half_w * 0.8660254037844386

        cx = px + half_w + half_w * self.CENTER_OFF_X
        cy = py + half_h + half_h * self.CENTER_OFF_Y

        wps = GeomVertexWriter(self._vdata, "i_pos_scale")
        wps.setRow(idx)
        wps.setData4f(float(cx), float(cy), float(pz + 0.01), half_w)

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

        atlas_w, atlas_h = self.icon_atlas.atlas_image.size

        def _norm(p: str) -> str:
            return p.replace("\\", "/").lstrip("/")

        uv_rects: List[Tuple[float, float, float, float]] = []
        for idx_slot, entry in enumerate(slots):
            if not entry or (isinstance(entry, BaseResource) and getattr(entry, "value", 0.0) == 0.0):
                uv_rects.append((0.0, 0.0, 0.0, 0.0))
                continue

            if idx_slot != 0 and isinstance(entry, BaseResource) and getattr(entry, "value", 0.0) > 0.0:
                entry = entry.get_numeric_icon() if hasattr(entry, "get_numeric_icon") else entry.icon

            if isinstance(entry, BaseResource):
                path = _norm(entry.icon) if hasattr(entry, "icon") else ""
            else:
                path = _norm(entry)

            if not path:
                uv_rects.append((0.0, 0.0, 0.0, 0.0))
                continue

            pos = self.icon_atlas.get_position_for_virtual_path(path)
            size = self.icon_atlas.get_dimensions_for_virtual_path(path)
            if not pos or not size:
                uv_rects.append((0.0, 0.0, 0.0, 0.0))
                continue
            x, y = pos
            w, h = size
            u0 = float(x) / float(atlas_w)
            v0 = 1.0 - float(y + h) / float(atlas_h)
            u1 = float(x + w) / float(atlas_w)
            v1 = 1.0 - float(y) / float(atlas_h)
            uv_rects.append((u0, v0, u1, v1))

        for s in range(self.ICON_SLOTS):
            name = f"i_uv{s}"
            w = GeomVertexWriter(self._vdata, name)
            w.setRow(idx)
            u0, v0, u1, v1 = uv_rects[s]
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
