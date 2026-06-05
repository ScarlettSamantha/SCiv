import math
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union, cast

from direct.task import Task
from gameplay.vision import VisionTileState, is_visible_for_render
from helpers.cache import Cache
from helpers.colors import Colors, Tuple4f
from helpers.geometry import generate_flat_top_hex_prism
from helpers.icons import Icons
from helpers.images import generate_city_nameplate, normalize_color_to_bytes, pil_image_to_panda3d_texture
from helpers.os import WindowsHelper
from helpers.placeholder import Placeholder
from managers.game import Game
from managers.i18n import I18nManager, T_TranslationOrStr, get_i18n
from managers.input import NET_NODE_TAG_ID_FIELD, NET_TYPE, NET_TYPE_FIELD
from panda3d.core import (
    AntialiasAttrib,
    BitMask32,
    CardMaker,
    Filename,
    NodePath,
    PandaNode,
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
from system.renderers.bits_renderer import BitsRenderer
from system.renderers.fog_of_war import FOGGED_TILE_TINT, UNSEEN_TILE_TINT
from system.tile_renderer import TileRendererSystem

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

    CHUNK_SIZE_X: int = 32
    CHUNK_SIZE_Y: int = 32
    _world_root: Optional[NodePath] = None
    _chunk_roots: Dict[Tuple[int, int], NodePath] = {}

    def __init__(self, tile: "Tile") -> None:
        self.tile: Tile = tile

        self.base = Cache.get_showbase_instance()
        self.game_manager: Game = Game.get_singleton_instance()

        self.anchor_node: NodePath = NodePath(f"tile_{tile.x}_{tile.y}_anchor")
        self.anchor_node.setCollideMask(BitMask32.bit(1))
        self.anchor_node.setTag(NET_TYPE_FIELD, str(NET_TYPE.TILE.value))
        self.anchor_node.setTag(NET_NODE_TAG_ID_FIELD, tile.tag)

        world_root: NodePath = self._get_world_root(self.base.render)
        chunk_root: NodePath = self._get_chunk_root(world_root, tile.x, tile.y)
        self.anchor_node.reparentTo(chunk_root)

        self.icon_atlas: AtlasGenerator = Cache.get_icon_atlas()

        self.geometry_node: NodePath = self.anchor_node.attachNewNode("geometry_group")
        self.geometry_node.setCollideMask(BitMask32.bit(1))
        self.geometry_node.setTag(NET_TYPE_FIELD, str(NET_TYPE.GEOM.value))
        self.geometry_node.setTag(NET_NODE_TAG_ID_FIELD, tile.tag)

        self.resource_model: Optional["Bit"] = None

        self.available_actions: List[str] = []
        self.ui_node: Optional[NodePath] = None

        self.city_ui_node: Optional[NodePath] = None
        self.healthbar_node: Optional[NodePath] = None
        self.build_queue_node: Optional[NodePath] = None
        self.population_node: Optional[NodePath] = None
        self.action_icons_nodes: List[NodePath] = []

        self.terrain_overlay_node: Optional[NodePath] = None
        self.unit_markers_node: Optional[NodePath] = None
        self.city_nameplate_node: Optional[NodePath] = None
        self.main_resource_icon_node: Optional[NodePath] = None
        self.models: List[NodePath] = []

        self.bits_renderer = BitsRenderer(tile, self.geometry_node)
        self.disable_yield_icons: bool = False

        self._fog_overlay_color: Optional[Tuple4f] = None
        self._visibility_state_applied: bool = False

        self._fog_overlay_color: Optional[Tuple4f] = None
        self._visibility_state_applied: bool = False

        shader_vertex_path: str = str(self.base.base_path / "assets" / "shaders" / "tile_selector.vert.glsl")
        shader_fragment_path: str = str(self.base.base_path / "assets" / "shaders" / "tile_selector.frag.glsl")

        if WindowsHelper.is_windows():
            shader_vertex_path = WindowsHelper.win32_to_unix_path(shader_vertex_path)
            shader_fragment_path = WindowsHelper.win32_to_unix_path(shader_fragment_path)

        self.selector_shader: Shader = Shader.load(
            Shader.SL_GLSL, vertex=shader_vertex_path, fragment=shader_fragment_path
        )
        self.selector_np: Optional[NodePath] = None
        self.selector_enabled: bool = False
        self.click_overlay_np: Optional[NodePath] = None
        self.fog_overlay_np: Optional[NodePath] = None
        self._fog_ceiling_z: float = float(self.tile.pos_z) + 0.1
        self._visibility_state: VisionTileState = VisionTileState.VISIBLE

        self.assets: P3DAssetArchive = Cache.get_asset_archive()

        TileRendererSystem.get().register_tile(self.tile)
        self._ensure_click_overlay()

    @classmethod
    def _get_world_root(cls, render: NodePath) -> NodePath:
        if cls._world_root is None or cls._world_root.is_empty():
            cls._world_root = render.attachNewNode("world_root")
            cls._world_root.setCollideMask(BitMask32.allOff())
        return cls._world_root

    @classmethod
    def _get_chunk_root(cls, world_root: NodePath, tile_x: int, tile_y: int) -> NodePath:
        cx = tile_x // cls.CHUNK_SIZE_X
        cy = tile_y // cls.CHUNK_SIZE_Y
        key: Tuple[int, int] = (cx, cy)
        node = cls._chunk_roots.get(key)
        if node is not None and not node.is_empty():
            return node

        node = world_root.attachNewNode(f"chunk_{cx}_{cy}")
        node.setCollideMask(BitMask32.allOff())
        cls._chunk_roots[key] = node
        return node

    def _ensure_click_overlay(self) -> None:
        if self.click_overlay_np is not None:
            return

        cm = CardMaker(f"tile_click_overlay_{self.tile.x}_{self.tile.y}")
        size = 1.0
        cm.setFrame(-size, size, -size, size)

        self.click_overlay_np = self.anchor_node.attachNewNode(cm.generate())
        self.click_overlay_np.setHpr(0, -90, 0)
        self.click_overlay_np.setPos(0, 0, 0.005)
        self.click_overlay_np.setTransparency(TransparencyAttrib.M_alpha)
        self.click_overlay_np.setDepthWrite(False)
        self.click_overlay_np.setBin("fixed", 5)
        self.click_overlay_np.setTag(NET_TYPE_FIELD, str(NET_TYPE.TILE.value))
        self.click_overlay_np.setTag(NET_NODE_TAG_ID_FIELD, self.tile.tag)
        self.click_overlay_np.setCollideMask(BitMask32.bit(1))
        self.click_overlay_np.hide()

    def _ensure_ui_node(self) -> NodePath:
        if self.ui_node is None:
            self.ui_node = self.anchor_node.attachNewNode("ui_group")
        return self.ui_node

    def _ensure_fog_overlay(self) -> NodePath:
        if self.fog_overlay_np is not None:
            return self.fog_overlay_np

        self.fog_overlay_np = generate_flat_top_hex_prism(radius=1.02, height=1.0)
        self.fog_overlay_np.reparentTo(self.anchor_node)
        self.fog_overlay_np.setHpr(30, 0, 0)
        self.fog_overlay_np.setPos(0, 0, -0.25)
        self.fog_overlay_np.setTransparency(TransparencyAttrib.M_alpha)
        self.fog_overlay_np.setDepthWrite(True)
        self.fog_overlay_np.setDepthTest(True)
        self.fog_overlay_np.setBin("fixed", 60)
        self.fog_overlay_np.setTwoSided(True)
        self._update_fog_overlay_transform()
        self.fog_overlay_np.hide()
        return self.fog_overlay_np

    def _update_fog_overlay_transform(self) -> None:
        if self.fog_overlay_np is None:
            return

        fog_height = max(0.3, self._fog_ceiling_z - float(self.tile.pos_z) + 0.25)
        self.fog_overlay_np.setPos(0, 0, -0.25)
        self.fog_overlay_np.setScale(1.0, 1.0, fog_height)

    def set_fog_ceiling_z(self, fog_ceiling_z: float) -> None:
        next_fog_ceiling_z = max(float(self.tile.pos_z), fog_ceiling_z)
        if abs(self._fog_ceiling_z - next_fog_ceiling_z) < 0.0001:
            return

        self._fog_ceiling_z = next_fog_ceiling_z
        self._update_fog_overlay_transform()

    def _show_fog_overlay(self, color: Tuple4f, *, transparent: bool) -> None:
        fog_overlay = self._ensure_fog_overlay()

        if transparent:
            fog_overlay.setDepthWrite(False)
            fog_overlay.setBin("transparent", 60)
        else:
            fog_overlay.setDepthWrite(True)
            fog_overlay.setBin("fixed", 60)

        if self._fog_overlay_color != color:
            fog_overlay.setColorScale(*color)
            self._fog_overlay_color = color

        if fog_overlay.isHidden():
            fog_overlay.show()

    def set_visibility_state(self, state: VisionTileState, *, force: bool = False) -> None:
        if not force and self._visibility_state_applied and self._visibility_state is state:
            return

        self._visibility_state = state
        self._visibility_state_applied = True
        fog_overlay = self.fog_overlay_np

        if state is VisionTileState.UNSEEN:
            self.anchor_node.show()
            self.geometry_node.hide()
            if self.ui_node is not None:
                self.ui_node.hide()
            if self.selector_np is not None:
                self.selector_np.hide()
            self._show_fog_overlay(UNSEEN_TILE_TINT, transparent=False)
            TileRendererSystem.get().hide_tile(self.tile)
            return

        self.anchor_node.show()

        if state is VisionTileState.FOGGED:
            self.geometry_node.hide()
            if self.ui_node is not None:
                self.ui_node.hide()
            if self.selector_np is not None:
                self.selector_np.hide()
            self._show_fog_overlay(FOGGED_TILE_TINT, transparent=True)
            TileRendererSystem.get().show_tile(self.tile)
            return

        if fog_overlay is not None:
            fog_overlay.hide()

        if is_visible_for_render(state):
            self.geometry_node.show()
            if self.ui_node is not None:
                self.ui_node.show()
            if self.selector_enabled and self.selector_np is not None:
                self.selector_np.show()
            TileRendererSystem.get().show_tile(self.tile)
            return

        self.geometry_node.hide()
        if self.ui_node is not None:
            self.ui_node.hide()
        if self.selector_np is not None:
            self.selector_np.hide()
        TileRendererSystem.get().hide_tile(self.tile)

    def _drop_ui_node_if_empty(self) -> None:
        if self.ui_node is None:
            return

        if len(self.ui_node.getChildren()) == 0:
            self.ui_node.removeNode()
            self.ui_node = None

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
        if self.ui_node is not None:
            for child in self.ui_node.getChildren():
                child.removeNode()
            self.ui_node.removeNode()

        self.ui_node = None
        self.terrain_overlay_node = None
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

        if self.fog_overlay_np is not None:
            self.fog_overlay_np.removeNode()
            self.fog_overlay_np = None

        if self.selector_np is not None:
            self.selector_np.removeNode()
            self.selector_np = None

        self.anchor_node.removeNode()
        self.geometry_node.removeNode()
        self.clear_models()
        self.base = None

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
            star_img=self.assets.get_panda3d_image("assets/icons/default/capital_icon.png"),
            star_offset_y=STAR_OFF_Y,
            star_offset_x=STAR_OFF_X,
            text_color=cast(Tuple4f, normalize_color_to_bytes(self.tile.get_owner().color)),
        )

        plate = plate.transpose(Image.FLIP_TOP_BOTTOM)  # type: ignore
        tex = pil_image_to_panda3d_texture(plate)

        MODEL_W = 2.5
        TARGET_WORLD_W = 0.75
        ar = plate.width / plate.height
        h = MODEL_W / ar

        cm = CardMaker(f"city_nameplate_{self.tile.get_tag()}")
        cm.setFrame(-MODEL_W / 2, MODEL_W / 2, -h / 2, h / 2)

        parent = self._ensure_ui_node()
        node: NodePath[PandaNode] = parent.attachNewNode(cm.generate())
        node.setTexture(tex)
        node.setTransparency(TransparencyAttrib.M_alpha)
        node.setPos(0, 0, 2.0)
        node.setBin("fixed", 90)
        node.setTwoSided(True)
        node.setAntialias(AntialiasAttrib.MAuto)
        node.setBillboardAxis()
        node.setScale(TARGET_WORLD_W / MODEL_W)

        self.city_nameplate_node = node

    def render(self, rerender_terrain: bool = False) -> None:
        self.anchor_node.setPos(*self.tile.get_cords())
        self.anchor_node.setScale(scale=1)
        self.clear_ui()
        self.prop_slots = self.tile.get_prop_slots()
        self._draw_improvements()
        TileRendererSystem.get().sync_tile(self.tile)

        if self.tile.city:
            if self.city_ui_node is None:
                self.city_ui_node = self._ensure_ui_node().attachNewNode("city_ui_group")
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
        self.set_visibility_state(self._visibility_state, force=True)

    def rerender_terrain(self) -> None:
        if self.game_manager.world_tile_grid is None:
            return
        self.game_manager.get_world_grid().update_tile(self.tile)

    def update(self) -> None:
        if not self.tile.city:
            if self.city_ui_node is not None:
                self.city_ui_node.removeNode()
                self.city_ui_node = None

            self._drop_ui_node_if_empty()
            TileRendererSystem.get().sync_tile(self.tile)
            self.set_visibility_state(self._visibility_state, force=True)
            return

        if self.city_ui_node is not None:
            self.city_ui_node.removeNode()

        self.city_ui_node = self._ensure_ui_node().attachNewNode("city_ui_group")
        self._draw_improvements()
        self._draw_city_ui()
        TileRendererSystem.get().sync_tile(self.tile)
        self.set_visibility_state(self._visibility_state, force=True)

    def _draw_city_ui(self) -> None:
        if not self.tile.city:
            return

        if self.city_ui_node is None:
            self.city_ui_node = self._ensure_ui_node().attachNewNode("city_ui_group")

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

    def on_unit_enter(self) -> None:
        if self.resource_model:
            self.bits_renderer.remove_bit(self.resource_model)

        self.render()

    def on_unit_leave(self) -> None:
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

        full_path = model_path
        self.last_result = None
        model_tpl: NodePath = self.assets.get_model(full_path)
        if not model_tpl:
            self.tile.logger.error(f"Model {full_path} could not be loaded.")
            return None

        parent_np: NodePath
        if parent is None:
            parent_np = self.geometry_node
        else:
            parent_np = parent

        x, y, z = pos_offset

        node: NodePath = model_tpl.instanceTo(parent_np)
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

        if flatten_model:
            node.clearModelNodes()
            node.flattenStrong()

        self.models.append(node)
        self.last_result = node
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
        return {"bits_renderer": self.bits_renderer.dump()}

    def load(self, data: Dict[str, Any]) -> None:
        bits_renderer_data = data.get("bits_renderer", {})
        if bits_renderer_data:
            self.bits_renderer.load(bits_renderer_data)
