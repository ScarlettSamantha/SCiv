import math
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from direct.task import Task
from gameplay.resource import BaseResource
from helpers.cache import Cache
from helpers.colors import Colors
from helpers.debug import Debug
from helpers.icons import Icons
from helpers.images import (
    generate_city_nameplate,
    normalize_color_to_bytes,
    pil_image_to_panda3d_texture,
)
from helpers.os import WindowsHelper
from helpers.placeholder import Placeholder
from managers.assets import AssetManager
from managers.game import Game
from managers.i18n import I18nManager, T_TranslationOrStr, get_i18n
from managers.input import NET_NODE_TAG_ID_FIELD, NET_TYPE, NET_TYPE_FIELD
from panda3d.core import (
    AntialiasAttrib,
    BitMask32,
    CardMaker,
    ColorBlendAttrib,
    Filename,
    NodePath,
    PandaNode,
    PointerToArray_float,
    PTAFloat,
    SamplerState,
    Shader,
    TextNode,
    Texture,
    TransparencyAttrib,
)
from PIL import Image
from PIL.ImageFont import FreeTypeFont
from system.asset_archive import P3DAssetArchive
from system.atlas import AtlasGenerator
from system.bits_renderer import BitsRenderer

if TYPE_CHECKING:
    from gameplay.bits import Bit
    from gameplay.city import City
    from gameplay.improvement import Improvement
    from gameplay.improvements.core.city.base_city_improvement import BaseCityImprovement
    from gameplay.tile import Tile
    from gameplay.unit import Unit


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
        self.game_manager: Game = Game.get_singleton_instance()
        self.atlas_width: int = 0
        self.atlas_height: int = 0

        self.anchor_node: NodePath = NodePath(f"tile_{tile.x}_{tile.y}_anchor")
        self.anchor_node.reparentTo(self.base.render)
        self.icon_atlas: AtlasGenerator = Cache.get_icon_atlas()

        self.geometry_node: NodePath = self.anchor_node.attachNewNode("geometry_group")
        self.anchor_node.reparentTo(self.base.render)
        self.geometry_node.set_collide_mask(BitMask32.bit(1))
        self.geometry_node.set_tag(NET_TYPE_FIELD, str(NET_TYPE.GEOM.value))
        self.geometry_node.set_tag(NET_NODE_TAG_ID_FIELD, tile.tag)
        self.resource_model: Optional["Bit"] = None

        self.available_actions: List[str] = []
        self.ui_node: NodePath = self.anchor_node.attachNewNode("ui_group")

        self.city_ui_node: Optional[NodePath] = None
        self.healthbar_node: Optional[NodePath] = None
        self.build_queue_node: Optional[NodePath] = None
        self.population_node: Optional[NodePath] = None
        self.action_icons_nodes: List[NodePath] = []

        self.terrain_overlay_node: Optional[NodePath] = None
        self.icon_overlay_node: Optional[NodePath] = None
        self.unit_markers_node: Optional[NodePath] = None
        self.city_nameplate_node: Optional[NodePath] = None
        self.main_resource_icon_node: Optional[NodePath] = None
        self.models: List[NodePath] = []

        self.bits_renderer = BitsRenderer(tile, self.geometry_node)
        self.disable_yield_icons: bool = False

        shader_vertex_path: str = str(self.base.base_path / "assets" / "shaders" / "tile_selector.vert.glsl")
        shader_fragment_path: str = str(self.base.base_path / "assets" / "shaders" / "tile_selector.frag.glsl")

        if WindowsHelper.is_windows():
            shader_vertex_path = WindowsHelper.win32_to_unix_path(shader_vertex_path)
            shader_fragment_path = WindowsHelper.win32_to_unix_path(shader_fragment_path)

        self.selector_shader = Shader.load(Shader.SL_GLSL, vertex=shader_vertex_path, fragment=shader_fragment_path)
        self.selector_np: Optional[NodePath] = None
        self.selector_enabled: bool = False

        self.assets: P3DAssetArchive = Cache.get_asset_archive()

    def _build_selector_quad(self) -> None:
        cm = CardMaker(f"tile_selector_{self.tile.x}_{self.tile.y}")
        size = 1.0

        cm.setFrame(-size, size, -size, size)
        cm.setUvRange((0, 0), (1, 1))

        self.selector_np = self.anchor_node.attachNewNode(cm.generate())
        self.selector_np.setHpr(0, -90, 0)
        self.selector_np.setTransparency(TransparencyAttrib.M_alpha)
        self.selector_np.setBin("fixed", 70)
        self.selector_np.setDepthWrite(False)
        self.selector_np.hide()

        self.selector_np.setShader(self.selector_shader)
        self.selector_np.setShaderInput("borderWidth", 0.03)  # type: ignore
        self.selector_np.setShaderInput("hexRadius", math.sqrt(3) / 2.05)  # type: ignore
        self.selector_np.setShaderInput("dashFreq", 18.0)  # type: ignore
        self.selector_np.setShaderInput("pulseSpeed", 2.0)  # type: ignore
        self.selector_np.setShaderInput("color", Colors.MAGENTA)  # type: ignore
        self.selector_np.setShaderInput("time", 0.0)  # type: ignore

        self.selector_np.setTag(NET_NODE_TAG_ID_FIELD, str(self.tile.tag))
        self.selector_np.setTag(NET_TYPE_FIELD, str(NET_TYPE.TILE.value))
        self.selector_np.setCollideMask(BitMask32.bit(1))

    def _update_selector_task(self, task: Task.Task) -> Task.Task:
        if not self.selector_enabled or self.selector_np is None:
            return Task.cont  # type: ignore
        self.selector_np.setShaderInput("time", task.time)  # type: ignore
        return Task.cont  # type: ignore

    def toggle_tile_selector(self, enable: bool) -> None:
        self.selector_enabled = enable
        if enable:
            self.on_select()
            if self.selector_np:
                if self.tile.owner is not None:
                    color = self.tile.get_owner().color
                else:
                    color = Colors.WHITE
                self.selector_np.setShaderInput("color", color)  # type: ignore
                self.selector_np.show()
        else:
            self.on_deselect()

    def on_select(self) -> None:
        if self.selector_np is None:
            self._build_selector_quad()
        self.base.taskMgr.add(self._update_selector_task, f"update-selector-{self.tile.tag}", delay=1 / 10)  # type: ignore
        self.update()

    def on_deselect(self) -> None:
        self.base.taskMgr.remove(f"update-selector-{self.tile.tag}")  # type: ignore
        if self.selector_np is not None:
            self.selector_np.removeNode()
            self.selector_np = None
        self.update()

    def clear_ui(self) -> None:
        for child in self.ui_node.getChildren():
            child.removeNode()

        self.terrain_overlay_node = None
        self.icon_overlay_node = None
        self.unit_markers_node = None
        self.city_nameplate_node = None

        if self.city_ui_node is not None:
            self.city_ui_node.removeNode()
        self.city_ui_node = None

        if self.main_resource_icon_node is not None:
            self.main_resource_icon_node.removeNode()

        self.main_resource_icon_node = None
        self.healthbar_node = None
        self.build_queue_node = None
        self.population_node = None
        self.action_icons_nodes = []

    def destroy(self) -> None:
        self.clear_ui()
        self.base.taskMgr.remove(f"update-selector-{self.tile.tag}")  # type: ignore
        if self.selector_np is not None:
            self.selector_np.removeNode()
            self.selector_np = None
        self.anchor_node.removeNode()
        self.geometry_node.removeNode()
        self.clear_models()
        self.base = None

    def render(self, rerender_terrain: bool = False) -> None:
        self.anchor_node.setPos(*self.tile.get_cords())
        self.anchor_node.setScale(scale=1)

        self.clear_ui()
        self.prop_slots = self.tile.get_prop_slots()

        self._draw_improvements()
        self._draw_yield_and_population_icons()

        if self.tile.city:
            if self.city_ui_node is None:
                self.city_ui_node = self.ui_node.attachNewNode("city_ui_group")
            self._draw_city_nameplate()
            self._draw_city_ui()

        if self.selector_np:
            self.selector_np.reparentTo(self.anchor_node)

        self.anchor_node.setTag(NET_TYPE_FIELD, str(NET_TYPE.TILE.value))
        self.anchor_node.setTag(NET_NODE_TAG_ID_FIELD, self.tile.tag)
        self.anchor_node.setCollideMask(BitMask32.bit(1))
        self.clear_models()

        if rerender_terrain:
            self.rerender_terrain()
        self.bits_renderer.render()

    def rerender_terrain(self) -> None:
        if self.game_manager.world_tile_grid is None:
            return
        self.game_manager.get_world_grid().update_tile(self.tile)

    def update(self) -> None:
        if not self.tile.city:
            if self.city_ui_node is not None:
                self.city_ui_node.removeNode()
                self.city_ui_node = None
            return

        if self.city_ui_node is not None:
            self.city_ui_node.removeNode()
        self.city_ui_node = self.ui_node.attachNewNode("city_ui_group")
        self._draw_improvements()
        self._draw_city_ui()

    def _draw_city_ui(self) -> None:
        if not self.tile.city:
            return

        if self.city_ui_node is None:
            self.city_ui_node = self.ui_node.attachNewNode("city_ui_group")

        parent: NodePath = self.city_ui_node

        i18n: I18nManager = get_i18n()
        city: "City" = self.tile.city
        self._draw_generic_bar(
            parent=parent,
            name=f"health_{city.name}",
            center_z=1.625,
            width=1.0,
            height=0.1,
            bg_color=(0.2, 0.2, 0.2, 0.8),
            fill_color=(0.0, 1.0, 0.0, 0.8),
            percentage=(city.health() / city.max_health if city.max_health else 0.0),
            text=f"HP: {round(city.health(), 0)}/{round(city.max_health, 0)}",
            text_scale=0.07,
            text_offset_z=-0.015,
            billboard=True,
        )

        icon_path = (
            Icons.population_icon_gaining() if city.calculate_food_surplus() >= 0 else Icons.population_icon_losing()
        )
        population_icon: Texture | None = self.icon_atlas.get_panda3d_texture_by_virtual_path(icon_path)

        if population_icon is not None:
            population_icon.setWrapU(Texture.WM_clamp)
            population_icon.set_format(Texture.F_srgb_alpha)
            population_icon.set_minfilter(SamplerState.FT_linear)

        population_gain_loss_text: T_TranslationOrStr = i18n.lookup(
            key="ui.player_ui.city.population_bar_label",
            formatting_parameters={
                "population": city.population,
                "food_collected": round(city.food_collected.food.value, 0),
                "food_required": round(city.new_population_food_required.food.value, 0),
            },
        )

        self._draw_generic_bar(
            parent=parent,
            name=f"pop_{city.name}",
            center_z=1.5,
            width=1,
            height=0.1,
            bg_color=(0.2, 0.2, 0.2, 0.8),
            fill_color=(1.0, 0.4, 0.7, 1.0),
            percentage=(city.food_collected.food.value / city.new_population_food_required.food.value),
            icon_texture=population_icon,
            icon_offset_x=-0.6,
            icon_size=(0.6, 0.6, 0.6),
            text=str(population_gain_loss_text),
            text_scale=0.07,
            text_offset_z=-0.015,
            billboard=True,
        )

        if city.is_building and city.building is not None:
            item: BaseCityImprovement | Unit | None = city.building
            icon_tex: Texture | None = self.icon_atlas.get_panda3d_texture_by_virtual_path(
                str(item.icon) if item.icon is not None else Placeholder.getPlaceholderImagePathSmallIcon()
            )

            assert icon_tex is not None, f"Icon texture for {item.icon} not found."

            icon_tex.setWrapU(Texture.WM_clamp)
            icon_tex.setWrapV(Texture.WM_clamp)
            icon_tex.setFormat(Texture.F_srgb_alpha)
            icon_tex.setMinfilter(SamplerState.FT_linear)
            icon_tex.setMagfilter(SamplerState.FT_linear)

            building_text: T_TranslationOrStr = i18n.lookup(
                key="ui.player_ui.city.building_bar_label",
                formatting_parameters={
                    "building": city.building.name if city.building else "None",
                    "resources_got": round(city.resource_collected.production.value, 0),
                    "resources_required": round(city.resource_required_amount.production.value, 0),
                },
            )

            self._draw_generic_bar(
                parent=parent,
                name=f"build_{city.name}",
                center_z=1.375,
                width=1,
                height=0.1,
                bg_color=(0.2, 0.2, 0.2, 1.0),
                fill_color=(0.0, 0.5, 1.0, 1.0),
                percentage=(city.resource_collected.production.value / city.resource_required_amount.production.value),
                text=building_text,
                icon_size=(0.6, 0.6, 0.6),
                icon_texture=icon_tex,
                icon_offset_x=-0.6,
                text_offset_z=-0.015,
                billboard=True,
            )
        icons = city.icons
        z = 1.2
        start_x = -0.7
        spacing = 0.2
        for idx, _icon in enumerate(icons):
            tex: Texture | None = self.icon_atlas.get_panda3d_texture_by_virtual_path(str(_icon))
            assert tex is not None, f"Icon texture for {self.tile.get_tag()} not found."
            cm = CardMaker(f"action_icon_{city.name}_{idx}")

            size = 0.12
            cm.setFrame(-size, size, -size, size)

            icon: NodePath[PandaNode] = parent.attachNewNode(cm.generate())
            icon.setTexture(tex)
            icon.setPos(start_x + idx * spacing, 0, z)
            self.action_icons_nodes.append(icon)

    def toggle_healthbar(self, enable: bool) -> None:
        if self.healthbar_node:
            if enable:
                self.healthbar_node.show()
            else:
                self.healthbar_node.hide()

    def _draw_generic_bar(
        self,
        parent: NodePath,
        name: str,
        center_z: float,
        width: float,
        height: float,
        bg_color: Tuple[float, float, float, float],
        fill_color: Tuple[float, float, float, float],
        percentage: float,
        icon_size: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        icon_texture: Optional[Texture] = None,
        icon_offset_x: float = 0.0,
        text: Optional[str] = None,
        text_scale: float = 0.06,
        text_offset_z: float = -0.015,
        billboard: bool = False,
    ) -> None:
        bar_group = parent.attachNewNode(f"{name}_group")
        bar_group.setPos(0, 0, center_z)

        if billboard:
            bar_group.setBillboardAxis()

        cm_bg = CardMaker(f"{name}_bg")
        cm_bg.setFrame(-width / 2, width / 2, -height / 2, height / 2)
        bg: NodePath[PandaNode] = bar_group.attachNewNode(cm_bg.generate())
        bg.setColor(*bg_color)
        bg.setTransparency(TransparencyAttrib.M_alpha)
        bg.setBin("fixed", 50)

        fill_w = width * max(0.0, min(1.0, percentage))
        cm_fg = CardMaker(f"{name}_fill")
        cm_fg.setFrame(-width / 2, -width / 2 + fill_w, -height / 2, height / 2)
        fg: NodePath[PandaNode] = bar_group.attachNewNode(cm_fg.generate())
        fg.setColor(*fill_color)
        fg.setTransparency(TransparencyAttrib.M_alpha)
        fg.setBin("fixed", 90)
        fg.setDepthTest(False)

        if icon_texture:
            cm_icon = CardMaker(f"{name}_icon")
            s = height
            cm_icon.setFrame(-s, s, -s, s)

            icon_np: NodePath[PandaNode] = bar_group.attachNewNode(cm_icon.generate())

            icon_texture.setFormat(Texture.F_srgb_alpha)
            icon_texture.setMinfilter(SamplerState.FT_linear)
            icon_texture.setMagfilter(SamplerState.FT_linear)

            icon_np.setTexture(icon_texture)
            icon_np.setColor(1, 1, 1, 1)
            icon_np.setTransparency(TransparencyAttrib.M_alpha)
            icon_np.setBin("fixed", 90)

            icon_np.setDepthTest(True)
            icon_np.setPos(icon_offset_x, 0, 0)
            icon_np.setScale(*icon_size)

        if text:
            tn = TextNode(f"{name}_text")
            tn.setText(text)
            tn.setAlign(TextNode.ACenter)
            tn_np: NodePath[TextNode] = bar_group.attachNewNode(tn)
            tn_np.setScale(text_scale)
            tn_np.setPos(0, 0, text_offset_z)
            tn_np.setBin("fixed", 90)
            tn_np.setDepthTest(False)

        if name.startswith("health_"):
            self.healthbar_node = bar_group
        elif name.startswith("build_"):
            self.build_queue_node = bar_group
        elif name.startswith("pop_"):
            self.population_node = bar_group

    def _draw_terrain_overlay(self) -> None:
        cm = CardMaker(f"terrain_overlay_{self.tile.get_tag()}")
        cm.setFrame(-1.0, 1.0, -1.0, 1.0)

        overlay: NodePath[PandaNode] = self.ui_node.attachNewNode(cm.generate())
        overlay.setTransparency(TransparencyAttrib.M_alpha)
        overlay.setAttrib(ColorBlendAttrib.makeOff())
        overlay.setBin("fixed", 40)
        overlay.setDepthTest(True)
        overlay.setDepthWrite(False)
        overlay.setHpr(0, -90, 0)
        overlay.setScale(1.0)
        overlay.setZ(0.001)
        overlay.setShaderOff()

        texture: Texture | None = Cache.get_terrain_atlas().get_panda3d_texture_by_virtual_path(
            str(self.tile.tile_terrain.texture())
        )

        if texture is None:
            self.tile.logger.error(f"Terrain texture not found for tile {self.tile.get_tag()}.")
            return

        texture.set_format(Texture.F_srgb_alpha)
        overlay.setTexture(texture, 1)
        self.terrain_overlay_node = overlay

    def is_city(self) -> bool:
        return self.tile.city is not None

    def get_city(self) -> "City":
        assert self.tile.city is not None, "Tile has no city."
        return self.tile.city

    def _render_improvements_as_bit(self, improvement: "Improvement") -> None:
        self.bits_renderer.add_bit(improvement.as_bit())

    def _draw_improvements(self) -> None:
        improvements = self.tile.get_improvements().get_all()
        if self.is_city():
            city: "City" = self.get_city()
            for improvement in city.get_improvements():
                if improvement not in improvements:
                    improvements.append(improvement)

        for improvement in improvements:  # type: ignore
            path: str | None = improvement.model
            if not path:
                continue
            self._render_improvements_as_bit(improvement)

    def _is_model_drawn(self) -> bool:
        return self.resource_model is not None

    def unload_resource_model(self) -> None:
        if self.resource_model is None:
            return
        self.bits_renderer.remove_bit(self.resource_model)

    def on_unit_enter(self):
        if self.resource_model:
            self.bits_renderer.remove_bit(self.resource_model)
        self.render()

    def on_unit_leave(self):
        if self.resource_model is not None:
            self.bits_renderer.add_bit(self.resource_model)
        self.render()

    def _load_texture_direct(self, path: str) -> Texture:
        if self.base is None:
            raise RuntimeError("Base instance is not available.")

        tex: Texture = self.base.loader.loadTexture(Filename(path))

        tex.setFormat(Texture.F_srgb_alpha)
        tex.setMinfilter(SamplerState.FT_linear)
        tex.setMagfilter(SamplerState.FT_linear)
        tex.setWrapU(Texture.WM_clamp)
        tex.setWrapV(Texture.WM_clamp)
        return tex

    def _draw_main_resource_icon(self, res: Union[BaseResource, str]) -> None:
        if isinstance(res, BaseResource):
            if getattr(res, "value", 0) == 0:
                return
            icon_path = str(res.icon) if hasattr(res, "icon") else None
        else:
            icon_path = str(res)
        if not icon_path:
            return

        tex: Texture = self._load_texture_direct(icon_path)

        cm = CardMaker(f"main_resource_icon_{self.tile.get_tag()}")
        s = 0.22
        cm.setFrame(-s, s, -s, s)

        np: NodePath[PandaNode] = self.ui_node.attachNewNode(cm.generate())
        np.setTexture(tex)
        np.setTransparency(TransparencyAttrib.M_alpha)
        np.setDepthTest(False)
        np.setBin("fixed", 85)
        np.setHpr(0, -90, 0)
        np.setScale(0.75)
        np.setShaderOff(1)

        pos = self.ICON_SLOT_POSITIONS["n"]
        np.setPos(pos[0], pos[1], pos[2] + 0.01)

        self.main_resource_icon_node = np

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
        icon_node.setDepthTest(False)
        icon_node.setDepthWrite(False)
        icon_node.setHpr(0, -90, 0)
        icon_node.setScale(0.75)

        atlas_tex: Texture = self.icon_atlas.get_panda3d_texture()
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

        if not self.disable_yield_icons:
            self.tile.calculate()
            base_yields = self.tile.get_tile_yield()
            slots: List[Union[str, BaseResource, None]]
            if self.tile.city:
                slots = [self.tile.city.get_population_icon()]
            else:
                res_list: List[BaseResource] = list(self.tile.resources.flatten().values())
                main_res: Optional[Union[str, BaseResource]] = res_list[0] if res_list else None
                if main_res is not None:
                    self._draw_main_resource_icon(main_res)
                slots = [None]

            slots += base_yields.export_basic()
            slots = slots[:7] + [None] * max(0, 7 - len(slots))

            self.atlas_width, self.atlas_height = self.icon_atlas.atlas_image.size
            uv_array: PointerToArray_float = PTAFloat.emptyArray(4 * 7)
            for idx, entry in enumerate(slots):
                if not entry or (isinstance(entry, BaseResource) and entry.value == 0.0):
                    base = idx * 4
                    uv_array[base + 0] = 0.0
                    uv_array[base + 1] = 0.0
                    uv_array[base + 2] = 0.0
                    uv_array[base + 3] = 0.0
                    continue

                if idx != 0 and isinstance(entry, BaseResource) and entry.value > 0.0:
                    entry = entry.get_numeric_icon() if hasattr(entry, "get_numeric_icon") else entry.icon
                if idx == 0 and not self.tile.city:
                    base = idx * 4
                    uv_array[base + 0] = 0.0
                    uv_array[base + 1] = 0.0
                    uv_array[base + 2] = 0.0
                    uv_array[base + 3] = 0.0
                    continue

                path = self._get_icon_virtual_path(entry, idx == 0 and not self.tile.city)
                if not path:
                    base = idx * 4
                    uv_array[base + 0] = 0.0
                    uv_array[base + 1] = 0.0
                    uv_array[base + 2] = 0.0
                    uv_array[base + 3] = 0.0
                    continue

                pos = self.icon_atlas.get_position_for_virtual_path(path)
                size = self.icon_atlas.get_dimensions_for_virtual_path(path)
                if not pos or not size:
                    base = idx * 4
                    uv_array[base + 0] = 0.0
                    uv_array[base + 1] = 0.0
                    uv_array[base + 2] = 0.0
                    uv_array[base + 3] = 0.0
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
        else:
            icon_node.set_shader_input("uv_rects", PTAFloat.emptyArray(4 * 7))  # type: ignore
            icon_node.set_shader_input("icon_count", 0)  # type: ignore

        icon_node.setZ(0.01)
        self.icon_overlay_node = icon_node

    def _get_icon_virtual_path(
        self,
        entry: Union[str, BaseResource],
        is_resource_slot: bool,
    ) -> Optional[str]:
        def _norm(p: str) -> str:
            p = p.replace("\\", "/")
            return p.lstrip("/")

        if isinstance(entry, str):
            return _norm(entry)

        if hasattr(entry, "get_numeric_icon") and getattr(entry, "value", 0) > 0:
            return _norm(entry.get_numeric_icon())

        if hasattr(entry, "icon"):
            return _norm(entry.icon)

        return None

    def _draw_city_nameplate(self) -> None:
        if not self.tile.city:
            return

        PLATE_PX_H = 192
        FONT_PX = max(48, int(PLATE_PX_H * 0.52))
        PAD_X = int(PLATE_PX_H * 0.10)
        PAD_Y = int(PLATE_PX_H * 0.06)
        TEXT_OFF_Y = int(PLATE_PX_H * 0.12)
        STAR_OFF_Y = TEXT_OFF_Y
        STAR_OFF_X = -int(PLATE_PX_H * 0.10)

        path_left: str = "assets/icons/default/city_plate_left.png"
        path_mid: str = "assets/icons/default/city_plate_middle.png"
        path_right: str = "assets/icons/default/city_plate_right.png"

        left: Image.Image = self.assets.get_panda3d_image(path_left)
        mid: Image.Image = self.assets.get_panda3d_image(path_mid)
        right: Image.Image = self.assets.get_panda3d_image(path_right)

        def _hfit(img: Image.Image, h: int) -> Image.Image:
            w = max(1, int(img.width * (h / img.height)))
            return img.resize((w, h), Image.LANCZOS)  # type: ignore

        left = _hfit(left, PLATE_PX_H)
        mid = _hfit(mid, PLATE_PX_H)
        right = _hfit(right, PLATE_PX_H)

        font: FreeTypeFont = self.assets.get_freetype_font("assets/fonts/Washington.ttf", FONT_PX)

        plate: Image.Image = generate_city_nameplate(
            left_img=left,
            middle_img=mid,
            right_img=right,
            city_name=str(self.tile.city.name),
            is_capital=self.tile.city.is_capital,
            font=font,
            padding=(PAD_X, PAD_Y),
            text_offset_y=TEXT_OFF_Y,
            star_img=self.assets.get_panda3d_image("assets/icons/default/capital_star.png"),
            star_offset_y=STAR_OFF_Y,
            star_offset_x=STAR_OFF_X,
            text_color=normalize_color_to_bytes(self.tile.get_owner().color),  # type: ignore[call-arg]
        )

        plate = plate.transpose(Image.FLIP_TOP_BOTTOM)  # type: ignore[no-untyped-call]
        tex = pil_image_to_panda3d_texture(plate)

        MODEL_W = 2.5
        TARGET_WORLD_W = 0.75

        ar = plate.width / plate.height
        h = MODEL_W / ar

        cm = CardMaker(f"city_nameplate_{self.tile.get_tag()}")
        cm.setFrame(-MODEL_W / 2, MODEL_W / 2, -h / 2, h / 2)

        node: NodePath[PandaNode] = self.ui_node.attachNewNode(cm.generate())
        node.setTexture(tex)
        node.setTransparency(TransparencyAttrib.M_alpha)
        node.setPos(0, 0, 2.0)
        node.setBin("fixed", 90)
        node.setTwoSided(True)
        node.setAntialias(AntialiasAttrib.MAuto)
        node.setBillboardAxis()

        node.setScale(TARGET_WORLD_W / MODEL_W)

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

        model_tpl: NodePath = AssetManager.load_model(full_path)
        if not model_tpl:
            self.tile.logger.error(f"Model {full_path} could not be loaded.")
            return None

        if parent is None:
            x = self.tile.pos_x + pos_offset[0]
            y = self.tile.pos_y + pos_offset[1]
            z = self.tile.pos_z + pos_offset[2]
        else:
            x, y, z = pos_offset

        node: NodePath = model_tpl.instanceTo(self.geometry_node)
        node.reparentTo(self.base.render if parent is None else parent)  # type: ignore
        node.setPos(x, y, z)
        node.setScale(max(0.01, scale))
        node.setHpr(*hpr)

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
        self.last_result = node
        if Debug.world_spawning():
            self.tile.logger.debug(f"Added model {model_path} to tile {self.tile.tag} at ({x},{y},{z}) scale {scale}.")

        return node

    def remove_model(self, net_id: str) -> None:
        remaining: List[NodePath] = []
        for model in self.models:
            if model.getTag(NET_NODE_TAG_ID_FIELD) == net_id:
                model.removeNode()
            else:
                remaining.append(model)
        self.models = remaining

    def clear_models(self) -> None:
        for model in self.models:
            model.removeNode()
        self.models.clear()

    def on_inspect(self, also_bits: bool = True) -> Dict[str, Union[str, int, float]]:
        loaded_models: List[str] = [str(model) for model in self.models]
        data: Dict[str, Union[str, int, float]] = {
            "loaded_models": ",".join(loaded_models) if loaded_models else "",
            "resource_model": str(self.resource_model.net_tag) if self.resource_model else "",
            "resource_model_pos": str(self.resource_model.offset) if self.resource_model else str((0.0, 0.0, 0.0)),
            "resource_model_scale": str(self.resource_model.scale) if self.resource_model else 1.0,
            "resource_model_hpr": str(self.resource_model.hpr) if self.resource_model else str((0.0, 0.0, 0.0)),
        }

        if also_bits and (bits := self.bits_renderer.on_inspect()):
            data["terrain_bits"] = bits.get("terrain_bits", "") or ""
            data["loaded_bits"] = bits.get("loaded_bits", "") or ""
            data["assigned_slots"] = bits.get("assigned_slots", "") or ""

        return data

    def dump(self) -> Dict[str, Any]:
        return {
            "bits_renderer": self.bits_renderer.dump(),
        }

    def load(self, data: Dict[str, Any]) -> None:
        bits_renderer_data = data.get("bits_renderer", {})
        if bits_renderer_data:
            self.bits_renderer.load(bits_renderer_data)
