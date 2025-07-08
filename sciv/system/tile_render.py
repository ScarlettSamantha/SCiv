"""
tile_renderer.py

Contains TileRenderer, responsible for visualizing a Tile in the game world
using Panda3D. Handles terrain and overlay cards, improvement models,
resource icons, unit markers, city nameplates, and model loading.
"""

import math
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union, cast

from direct.task import Task
from gameplay.bits import BitsRenderer
from gameplay.resource import BaseResource
from helpers.cache import Cache
from helpers.colors import Colors, Tuple4f
from helpers.debug import Debug
from helpers.images import (
    generate_city_nameplate,
    normalize_color_to_bytes,
    pil_image_to_panda3d_texture,
)
from helpers.os import WindowsHelper
from managers.assets import AssetManager
from managers.game import Game
from managers.input import NET_NODE_TAG_ID_FIELD, NET_TYPE, NET_TYPE_FIELD
from panda3d.core import (
    AntialiasAttrib,
    BitMask32,
    CardMaker,
    ColorBlendAttrib,
    NodePath,
    PandaNode,
    PTAFloat,
    SamplerState,
    Shader,
    Texture,
    TransparencyAttrib,
)
from PIL import Image
from PIL.ImageFont import FreeTypeFont
from system.atlas import AtlasGenerator

if TYPE_CHECKING:
    from gameplay.tile import Tile


class TileRenderer:
    ICON_SLOT_POSITIONS = {
        "center": (0.0, 0.0, 0),
        "n": (0.0, 0.45, 0),
        "ne": (0.375, 0.35, 0),
        "e": (0.45, 0.0, 0),
        "se": (0.375, -0.35, 0),
        "s": (0.0, -0.45, 0),
        "sw": (-0.375, -0.35, 0),
        "w": (-0.45, 0.0, 0),
        "nw": (-0.375, 0.35, 0),
    }

    def __init__(self, tile: "Tile") -> None:
        self.tile: Tile = tile
        self.base = Cache.get_showbase_instance()
        self.atlas_width: int = 0
        self.atlas_height: int = 0

        # Root anchor for all geometry and UI nodes
        self.anchor_node: NodePath = NodePath(f"tile_{tile.x}_{tile.y}_anchor")
        self.anchor_node.reparentTo(self.base.render)
        self.icon_atlas: AtlasGenerator = Cache.get_icon_atlas()
        # Geometry group: terrain, walls, improvements, models
        self.geometry_node: NodePath = self.anchor_node.attachNewNode("geometry_group")
        self.anchor_node.reparentTo(self.base.render)
        self.geometry_node.set_collide_mask(BitMask32.bit(1))
        self.geometry_node.set_tag(NET_TYPE_FIELD, str(NET_TYPE.GEOM.value))
        self.geometry_node.set_tag(NET_NODE_TAG_ID_FIELD, tile.tag)
        self.resource_model: Optional[NodePath] = None

        # UI group: overlays, icons, unit markers, city nameplate
        self.ui_node: NodePath = self.anchor_node.attachNewNode("ui_group")

        # Dynamic nodes
        self.terrain_overlay_node: Optional[NodePath] = None
        self.icon_overlay_node: Optional[NodePath] = None
        self.unit_markers_node: Optional[NodePath] = None
        self.city_nameplate_node: Optional[NodePath] = None
        self.models: List[NodePath] = []

        self.bits_renderer = BitsRenderer(tile, self.geometry_node)

        shader_vertex_path: str = str(self.base.base_path / "assets" / "shaders" / "tile_selector.vert.glsl")
        shader_fragment_path: str = str(self.base.base_path / "assets" / "shaders" / "tile_selector.frag.glsl")

        if WindowsHelper.is_windows():
            shader_vertex_path = WindowsHelper.win32_to_unix_path(shader_vertex_path)
            shader_fragment_path = WindowsHelper.win32_to_unix_path(shader_fragment_path)

        # shader for tile selection
        self.selector_shader = Shader.load(Shader.SL_GLSL, vertex=shader_vertex_path, fragment=shader_fragment_path)
        self.selector_np: Optional[NodePath] = None
        self.selector_enabled: bool = False

        self._build_selector_quad()

    def _build_selector_quad(self) -> None:
        cm = CardMaker(f"tile_selector_{self.tile.x}_{self.tile.y}")
        size = 1.0
        cm.setFrame(-size, size, -size, size)
        cm.setUvRange((0, 0), (1, 1))  # ensure we get uv coords

        self.selector_np = self.anchor_node.attachNewNode(cm.generate())
        self.selector_np.setHpr(0, -90, 0)
        self.selector_np.setTransparency(TransparencyAttrib.M_alpha)
        self.selector_np.setBin("fixed", 70)
        self.selector_np.setDepthWrite(False)
        self.selector_np.hide()

        # apply our flat-top hex shader
        self.selector_np.setShader(self.selector_shader)

        # border thickness in UV-space (0–1), dash count & speed
        self.selector_np.setShaderInput("borderWidth", 0.03)  #  type: ignore
        self.selector_np.setShaderInput(  # type: ignore
            "hexRadius", math.sqrt(3) / 2.05
        )  # Just a bit of offset from the hex radius # type: ignore
        self.selector_np.setShaderInput("dashFreq", 18.0)  # type: ignore
        self.selector_np.setShaderInput("pulseSpeed", 2.0)  # type: ignore
        self.selector_np.setShaderInput("color", (1.0, 1.0, 1.0, 1.0))  # type: ignore
        self.selector_np.setShaderInput("time", 0.0)  # type: ignore

        self.selector_np.setTag(NET_NODE_TAG_ID_FIELD, str(self.tile.tag))
        self.selector_np.setTag(NET_TYPE_FIELD, str(NET_TYPE.TILE.value))
        self.selector_np.setCollideMask(BitMask32.bit(1))

    def _update_selector_task(self, task: Task.Task) -> Task.Task:
        if not self.selector_enabled or self.selector_np is None:
            return Task.cont  # type: ignore
        # update time uniform
        self.selector_np.setShaderInput("time", task.time)  #    type: ignore
        return Task.cont  # type: ignore

    def toggle_tile_selector(self, enable: bool) -> None:
        self.selector_enabled = enable
        if self.selector_np:
            if enable:
                self.on_select()
                if self.tile.owner is not None:
                    color = self.tile.get_owner().color[:3]
                else:
                    color = Colors.WHITE[:3]
                self.selector_np.setShaderInput("color", color)  # type: ignore
                self.selector_np.show()
            else:
                self.selector_np.hide()
                self.on_deselect()

    def on_select(self) -> None:
        self.base.taskMgr.add(self._update_selector_task, f"update-selector-{self.tile.tag}", delay=1 / 10)  # type: ignore

    def on_deselect(self) -> None:
        self.base.taskMgr.remove(f"update-selector-{self.tile.tag}")  # type: ignore

    def clear_ui(self) -> None:
        for child in self.ui_node.getChildren():
            child.removeNode()
        self.terrain_overlay_node = None
        self.icon_overlay_node = None
        self.unit_markers_node = None
        self.city_nameplate_node = None

    def destroy(self) -> None:
        self.clear_ui()
        self.anchor_node.removeNode()
        self.geometry_node.removeNode()
        self.clear_models()
        self.base = None

    def render(self, update_yields: bool = True) -> None:
        if update_yields:
            self.tile.calculate()  # type: ignore

        self.anchor_node.setPos(*self.tile.get_cords())
        self.anchor_node.setScale(1)

        self.clear_ui()

        self._draw_terrain_overlay()
        self._draw_improvements()

        self._draw_resource_model()

        self._draw_yield_and_population_icons()

        self._draw_city_nameplate()

        self.bits_renderer.render()

        if self.selector_np:
            self.selector_np.reparentTo(self.anchor_node)

        # self.geometry_node.flatten_medium()

        self.anchor_node.setTag(NET_TYPE_FIELD, str(NET_TYPE.TILE.value))
        self.anchor_node.setTag(NET_NODE_TAG_ID_FIELD, self.tile.tag)
        self.anchor_node.setCollideMask(BitMask32.bit(1))

    def _draw_terrain_overlay(self) -> None:
        cm = CardMaker(f"terrain_overlay_{self.tile.get_tag()}")
        cm.setFrame(-1.0, 1.0, -1.0, 1.0)
        overlay = self.ui_node.attachNewNode(cm.generate())
        overlay.setTransparency(TransparencyAttrib.M_alpha)
        overlay.setAttrib(ColorBlendAttrib.makeOff())
        overlay.setBin("fixed", 40)
        overlay.setDepthTest(True)
        overlay.setDepthWrite(False)
        overlay.setHpr(0, -90, 0)
        overlay.setScale(1.0)
        overlay.setZ(0.001)
        overlay.setShaderOff()

        texture = Cache.get_terrain_atlas().get_panda3d_texture_by_virtual_path(str(self.tile.tile_terrain.texture()))

        if texture is None:
            self.tile.logger.error(f"Terrain texture not found for tile {self.tile.get_tag()}.")
            return
        texture.set_format(Texture.F_srgb_alpha)

        overlay.setTexture(texture, 1)

        color = Colors.to_normalized_float(self.tile.tile_terrain.wall_color(), 1.0)
        mesh = Game.get_singleton_instance().get_mesh()
        mesh.set_wall_color_for_tile(
            mesh.get_tile_index_from_coords(self.tile.x, self.tile.y),
            cast(Tuple4f, color),
        )
        self.terrain_overlay_node = overlay

    def is_city(self) -> bool:
        return self.tile.city is not None

    def _draw_improvements(self) -> None:
        for improvement in self.tile.improvements().get_all():
            path = improvement.model
            if not path:
                continue
            self.add_model(
                model_path=path,
                net_type=NET_TYPE.IMPROVEMENT,
                pos_offset=improvement.get_model_offset(),
                scale=improvement.get_model_scale(),
                hpr=improvement.get_model_hpr(),
            )

    def _draw_resource_model(self) -> None:
        if not (res_list := list(self.tile.resources.flatten_non_mechanic().values())):
            return

        if self.tile.is_city() or self.tile.block_resource_model_spawning is True or self.tile.units.has_any():
            self.unload_resource_model()
            return

        resource = res_list[0]

        model_def = resource.get_land_model() if self.tile.is_land else resource.get_water_model()

        if model_def:
            self.resource_model = self.add_model(
                model_path=model_def,
                net_type=NET_TYPE.RESOURCE,
                pos_offset=resource.model_position,
                scale=resource.model_size,
                hpr=resource.model_hpr,
                disable_lighting=resource.model_disable_default_lighting,
                disable_shader=resource.model_disable_default_shader,
                net_id=self.tile.tag,  # Use the resource icon as a unique identifier
                parent=self.geometry_node,
                flatten_model=False,
            )

    def _is_model_drawn(self) -> bool:
        return self.resource_model is not None

    def unload_resource_model(self) -> None:
        if self.resource_model is None:
            return
        self.resource_model.remove_node()
        self.resource_model = None

    def on_unit_enter(self):
        if self.resource_model:
            self.resource_model.hide()

    def on_unit_leave(self):
        if self.resource_model:
            self.resource_model.show()

    def _draw_yield_and_population_icons(self) -> None:
        if self.base is None:
            return

        cm = CardMaker(f"icon_overlay_{self.tile.get_tag()}")
        cm.setFrame(-1.0, 1.0, -1.0, 1.0)
        cm.setHasUvs(True)
        icon_node = self.ui_node.attachNewNode(cm.generate())
        icon_node.setTransparency(TransparencyAttrib.M_alpha)
        icon_node.setAttrib(ColorBlendAttrib.makeOff())
        icon_node.setBin("fixed", 60)
        icon_node.setDepthTest(True)
        icon_node.setDepthWrite(False)
        icon_node.setHpr(0, -90, 0)
        icon_node.setScale(0.75)

        atlas_tex = self.icon_atlas.get_panda3d_texture()
        atlas_tex.setWrapU(Texture.WM_clamp)
        atlas_tex.setWrapV(Texture.WM_clamp)
        atlas_tex.setFormat(Texture.F_srgb_alpha)
        atlas_tex.setMinfilter(SamplerState.FT_linear)
        atlas_tex.setMagfilter(SamplerState.FT_linear)
        icon_node.setShader(
            Shader.load(
                Shader.SL_GLSL,
                self.base.base_path / "assets/shaders/resource_icons.vert.glsl",
                self.base.base_path / "assets/shaders/resource_icons.frag.glsl",
            )
        )
        icon_node.set_shader_input("icon_atlas", atlas_tex)  # type: ignore

        # Prepare slots: population or first resource + base yields
        base_yields = self.tile.get_tile_yield()
        if self.tile.city:
            slots: List[Union[str, BaseResource, None]] = [
                self.tile.city.get_population_icon(),
            ]
        else:
            res_list = list(self.tile.resources.flatten().values())
            slots = [res_list[0] if res_list else None]
        slots += base_yields.export_basic()
        slots = slots[:7] + [None] * max(0, 7 - len(slots))

        self.atlas_width, self.atlas_height = self.icon_atlas.atlas_image.size
        uv_array = PTAFloat.emptyArray(4 * 7)
        for idx, entry in enumerate(slots):
            if not entry or (isinstance(entry, BaseResource) and entry.value == 0.0):
                continue

            if idx != 0 and isinstance(entry, BaseResource) and entry.value > 0.0:
                # If it's a resource with a value, we use its icon
                entry = entry.get_numeric_icon() if hasattr(entry, "get_numeric_icon") else entry.icon

            path = self._get_icon_virtual_path(entry, idx == 0 and not self.tile.city)
            if not path:
                continue

            pos = self.icon_atlas.get_position_for_virtual_path(path)
            size = self.icon_atlas.get_dimensions_for_virtual_path(path)

            if not pos or not size:
                continue

            x, y = pos
            w, h = size
            u0, v1 = x / self.atlas_width, 1.0 - (y / self.atlas_height)
            u1, v0 = (x + w) / self.atlas_width, 1.0 - ((y + h) / self.atlas_height)
            base = idx * 4
            uv_array[base + 0] = u0
            uv_array[base + 1] = v0
            uv_array[base + 2] = u1
            uv_array[base + 3] = v1

        icon_node.set_shader_input("uv_rects", uv_array)  # type: ignore
        icon_node.set_shader_input("icon_count", 7)  # type: ignore
        icon_node.setZ(0.01)
        self.icon_overlay_node = icon_node

    def _get_icon_virtual_path(
        self,
        entry: Union[str, BaseResource],
        is_resource_slot: bool,
    ) -> Optional[str]:
        """
        Determine the atlas path for a given slot entry (population or resource/yield).
        """
        if isinstance(entry, str):
            return entry.replace("resources/", "")
        if hasattr(entry, "icon"):
            return entry.icon.replace("assets/icons/", "")
        if hasattr(entry, "get_numeric_icon") and getattr(entry, "value", 0) > 0:
            return entry.get_numeric_icon().replace("resources/", "")
        return None

    def _draw_city_nameplate(self) -> None:
        """Generate a billboarding nameplate for the city on this tile."""
        if not self.tile.city:
            return
        atlas: AtlasGenerator = self.icon_atlas

        path_left: Path | None | str = atlas.get_real_path_for_virtual_path("city_plate_left.png")
        path_mid: Path | None | str = atlas.get_real_path_for_virtual_path("city_plate_middle.png")
        path_right: Path | None | str = atlas.get_real_path_for_virtual_path("city_plate_right.png")

        if WindowsHelper.is_windows():
            # Convert to Unix path if not on Windows
            path_left = WindowsHelper.unix_to_win32_path(str(path_left))
            path_mid = WindowsHelper.unix_to_win32_path(str(path_mid))
            path_right = WindowsHelper.unix_to_win32_path(str(path_right))

        left: Image.Image = AssetManager.load_pil_image(str(path_left))
        mid: Image.Image = AssetManager.load_pil_image(str(path_mid))
        right: Image.Image = AssetManager.load_pil_image(str(path_right))
        font: FreeTypeFont = AssetManager.load_pil_font("assets/fonts/Washington.ttf", size=224)

        plate: Image.Image = generate_city_nameplate(
            left_img=left,
            middle_img=mid,
            right_img=right,
            city_name=str(self.tile.city.name),
            is_capital=self.tile.city.is_capital,
            font=font,
            padding=(20, 8),
            text_offset_y=32,
            star_img=atlas.get_pil_image_by_virtual_path("capital_icon.png"),
            star_offset_y=32,
            star_offset_x=-16,
            text_color=normalize_color_to_bytes(self.tile.get_owner().color),  # type: ignore[call-arg]
        )
        plate = plate.transpose(
            Image.FLIP_TOP_BOTTOM  # type: ignore[no-untyped-call]
        )  # Flip for Panda3D's coordinate system # type: ignore[no-untyped-call]
        tex = pil_image_to_panda3d_texture(plate)

        cm = CardMaker(f"city_nameplate_{self.tile.get_tag()}")
        ar = plate.width / plate.height
        w = 2.5
        h = w / ar
        cm.setFrame(-w / 2, w / 2, -h / 2, h / 2)
        node: NodePath[PandaNode] = self.ui_node.attachNewNode(cm.generate())
        node.setTexture(tex)
        node.setTransparency(TransparencyAttrib.M_alpha)
        node.setPos(0, 0, 2.0)
        node.setScale(0.75)
        node.setBin("fixed", 50)
        node.setTwoSided(True)
        node.setAntialias(AntialiasAttrib.MAuto)
        node.setBillboardAxis()
        self.city_nameplate_node = node

    def add_model(
        self,
        model_path: str,
        net_type: NET_TYPE,
        pos_offset: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        scale: float = 1.0,
        hpr: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        net_id: Optional[str] = None,
        disable_lighting: bool = False,
        disable_shader: bool = False,
        parent: Optional[NodePath] = None,
        flatten_model: bool = False,
    ) -> Optional[NodePath]:
        if self.base is None:
            raise ValueError("TileRenderer base is not initialized.")

        full_path = str(Path(self.base.get_base_path()).joinpath(model_path).absolute())
        self.last_result = None

        loaded_model: NodePath[PandaNode] = AssetManager.load_model(full_path)

        if not loaded_model:
            self.tile.logger.error(f"Model {full_path} could not be loaded.")
            return None

        if parent is None:
            x = self.tile.pos_x + pos_offset[0]
            y = self.tile.pos_y + pos_offset[1]
            z = self.tile.pos_z + pos_offset[2]
        else:
            x, y, z = pos_offset

        loaded_model.setScale(max(0.01, scale))
        loaded_model.setHpr(*hpr)

        node: NodePath[PandaNode] = loaded_model.instanceTo(self.geometry_node)

        if flatten_model:
            node.flatten_medium()

        node.reparentTo(self.base.render if parent is None else parent)  # type: ignore
        node.setPos(x, y, z)
        node.setCollideMask(BitMask32.bit(1))
        node.setTag(NET_TYPE_FIELD, str(net_type.value))

        if disable_lighting:
            node.setLightOff()
        if disable_shader:
            node.setShaderOff()

        if net_id is not None:
            node.setTag(NET_NODE_TAG_ID_FIELD, net_id)
        else:
            node.setTag(NET_NODE_TAG_ID_FIELD, self.tile.tag)

        self.models.append(node)
        self.last_result: Optional[NodePath[PandaNode]] = node
        if Debug.world_spawning():
            self.tile.logger.debug(f"Added model {model_path} to tile {self.tile.tag} at ({x},{y},{z}) scale {scale}.")

        return node

    def remove_model(self, net_id: str) -> None:
        for model in self.models[:]:
            model.removeNode()

    def clear_models(self) -> None:
        for model in self.models:
            model.removeNode()
        self.models.clear()

    def on_inspect(self, also_bits: bool = True) -> Dict[str, Union[str, int, float]]:
        loaded_models: List[str] = [str(model) for model in self.models]

        data: Dict[str, Union[str, int, float]] = {  # Otherwise mypy complains about the type they are all strings
            "loaded_models": ",".join(loaded_models) if loaded_models else "",
            "resource_model": str(self.resource_model.get_name()) if self.resource_model else "",
            "resource_model_pos": str(self.resource_model.getPos()) if self.resource_model else str((0.0, 0.0, 0.0)),
            "resource_model_scale": str(self.resource_model.getScale()) if self.resource_model else 1.0,
            "resource_model_hpr": str(self.resource_model.getHpr()) if self.resource_model else str((0.0, 0.0, 0.0)),
        }

        if also_bits and (bits := self.bits_renderer.on_inspect()):
            data["terrain_bits"] = bits.get("terrain_bits", "") or ""
            data["loaded_bits"] = bits.get("loaded_bits", "") or ""
            data["assigned_slots"] = bits.get("assigned_slots", "") or ""

        return data
