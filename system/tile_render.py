"""
tile_renderer.py

Contains TileRenderer, responsible for visualizing a Tile in the game world
using Panda3D. Handles terrain and overlay cards, improvement models,
resource icons, unit markers, city nameplates, and model loading.
"""

from typing import TYPE_CHECKING, Optional, Tuple, List, Union, cast
from pathlib import Path
from PIL import Image

from panda3d.core import (
    AntialiasAttrib,
    BitMask32,
    CardMaker,
    ColorBlendAttrib,
    NodePath,
    PTAFloat,
    SamplerState,
    Shader,
    Texture,
    TransparencyAttrib,
)

from gameplay.unit_icons import UnitIcons
from helpers.cache import Cache
from helpers.colors import Colors, Tuple4f
from helpers.images import (
    normalize_color_to_bytes,
    generate_city_nameplate,
    pil_image_to_panda3d_texture,
)
from helpers.debug import Debug
from system.atlas import AtlasGenerator
from gameplay._units import Units
from gameplay.resource import BaseResource
from managers.assets import AssetManager
from managers.input import NET_NODE_TAG_ID_FIELD, NET_TYPE, NET_TYPE_FIELD
from managers.game import Game
from gameplay.bits import BitsRenderer

if TYPE_CHECKING:
    from gameplay.tile import Tile


class TileRenderer:
    """
    Encapsulates all Panda3D rendering logic for a Tile instance.

    Responsibilities:
      - Draw terrain overlay with correct texture and wall color.
      - Render improvement models on the tile.
      - Place resource models where appropriate.
      - Display yield and population icons from an icon atlas.
      - Show markers for units present on the tile.
      - Draw a city nameplate when a city occupies the tile.
      - Load and attach 3D models via Panda3D loader.
    """

    ICON_SLOT_POSITIONS = {
        "center": (0.0, 0.0, 0.3),
        "n": (0.0, 0.45, 0.3),
        "ne": (0.375, 0.35, 0.3),
        "e": (0.45, 0.0, 0.3),
        "se": (0.375, -0.35, 0.3),
        "s": (0.0, -0.45, 0.3),
        "sw": (-0.375, -0.35, 0.3),
        "w": (-0.45, 0.0, 0.3),
        "nw": (-0.375, 0.35, 0.3),
    }

    def __init__(self, tile: "Tile") -> None:
        self.tile = tile
        self.base = Cache.get_showbase_instance()
        self.icon_atlas: AtlasGenerator = Cache.get_icon_atlas()
        self.atlas_width: int = 0
        self.atlas_height: int = 0

        # Root anchor for all geometry and UI nodes
        self.anchor_node: NodePath = NodePath(f"tile_{tile.x}_{tile.y}_anchor")
        self.anchor_node.reparentTo(self.base.render)

        # Geometry group: terrain, walls, improvements, models
        self.geometry_node: NodePath = self.anchor_node.attachNewNode("geometry_group")
        self.anchor_node.reparentTo(self.base.render)
        self.geometry_node.set_collide_mask(BitMask32.bit(1))
        self.geometry_node.set_tag(NET_TYPE_FIELD, str(NET_TYPE.GEOM.value))
        self.geometry_node.set_tag(NET_NODE_TAG_ID_FIELD, tile.tag)

        # UI group: overlays, icons, unit markers, city nameplate
        self.ui_node: NodePath = self.anchor_node.attachNewNode("ui_group")

        # Helpers
        self.unit_icon_helper = Units()
        self.unit_icons: Optional[UnitIcons] = None

        # Dynamic nodes
        self.terrain_overlay_node: Optional[NodePath] = None
        self.icon_overlay_node: Optional[NodePath] = None
        self.unit_markers_node: Optional[NodePath] = None
        self.city_nameplate_node: Optional[NodePath] = None
        self.models: List[NodePath] = []

        self.bits_renderer = BitsRenderer(tile)
        self.unit_icons = UnitIcons(self.ui_node)

    def clear_ui(self) -> None:
        """Remove all child nodes under the UI group."""
        for child in self.ui_node.getChildren():
            child.removeNode()
        self.terrain_overlay_node = None
        self.icon_overlay_node = None
        self.unit_markers_node = None
        self.city_nameplate_node = None

    def render(self, update_yields: bool = True) -> None:
        """
        Redraw the entire tile each frame or when its state changes.
        """
        if update_yields:
            self.tile.calculate()

        # Position and scale tile root
        self.anchor_node.setPos(self.tile.pos_x, self.tile.pos_y, self.tile.pos_z)
        self.anchor_node.setScale(1)

        # Clear previous UI elements
        self.clear_ui()

        # Draw base terrain and geometry
        self._draw_terrain_overlay()
        self._draw_improvements()

        # Draw resource model if no city occupies the tile
        self._draw_resource_model()

        # Draw yield and population icons
        self._draw_yield_and_population_icons()

        # Draw units and city nameplate
        self._draw_unit_markers()
        self._draw_city_nameplate()

        # Only render bits overlays when the tile is not occupied by a city
        self.bits_renderer.render()

        # Optimize node hierarchy
        self.anchor_node.flatten_medium()
        self.geometry_node.flatten_medium()

        # Network tagging for selection/clicks
        self.anchor_node.setTag(NET_TYPE_FIELD, str(NET_TYPE.TILE.value))
        self.anchor_node.setTag(NET_NODE_TAG_ID_FIELD, self.tile.tag)
        self.anchor_node.setCollideMask(BitMask32.bit(1))

    def _draw_terrain_overlay(self) -> None:
        """Render the flat overlay showing terrain texture and wall color."""
        cm = CardMaker(f"terrain_overlay_{self.tile.id}")
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

        texture = Cache.get_terrain_atlas().get_panda3d_texture_by_virtual_path(str(self.tile.tile_terrain.texture()))

        if texture is None:
            self.tile.logger.error(f"Terrain texture not found for tile {self.tile.id}.")
            return

        overlay.setTexture(texture, 1)

        color = Colors.to_normalized_float(self.tile.tile_terrain.wall_color(), 1.0)
        mesh = Game.get_singleton_instance().get_mesh()
        mesh.set_wall_color_for_tile(
            mesh.get_tile_index_from_coords(self.tile.x, self.tile.y),
            cast(Tuple4f, color),
        )
        self.terrain_overlay_node = overlay

    def _draw_improvements(self) -> None:
        """Place each improvement's 3D model on the geometry group."""
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
        """Render a resource 3D model if present on the tile."""
        if self.tile.city is not None or self.tile.block_resource_model_spawning is True:
            return

        if not (res_list := list(self.tile.resources.flatten_non_mechanic().values())):
            return

        resource = res_list[0]

        model_def = (
            resource.get_land_model() if self.tile.is_land and not self.tile.is_coast else resource.get_water_model()
        )

        if model_def:
            self.add_model(
                model_path=model_def,
                net_type=NET_TYPE.RESOURCE,
                pos_offset=resource.model_position,
                scale=resource.model_size,
                hpr=resource.model_hpr,
            )

    def _is_model_drawn(self, model_path: str) -> bool:
        """
        Check if a model with the given path is already drawn on this tile.
        Returns True if the model is found, False otherwise.
        """
        for child in self.geometry_node.getChildren():
            if child.getTag(NET_TYPE_FIELD) == str(NET_TYPE.RESOURCE.value):
                if child.getTag(NET_NODE_TAG_ID_FIELD) == model_path:
                    return True
        return False

    def _draw_yield_and_population_icons(self) -> None:
        """Generate a UV card showing population and yield icons from the atlas."""
        cm = CardMaker(f"icon_overlay_{self.tile.id}")
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
                "assets/shaders/resource_icons.vert.glsl",
                "assets/shaders/resource_icons.frag.glsl",
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

    def _draw_unit_markers(self) -> None:
        """Add small icons above the tile for each unit present."""
        node = self.ui_node.attachNewNode("unit_markers")
        for unit in self.tile.units.all():
            if unit.icon and self.unit_icons is not None:
                self.unit_icons.add_marker(
                    (self.tile.pos_x, self.tile.pos_y, self.tile.pos_z + 1.5),  # world offset
                    (0.2, 0.2),  # icon size
                    str(unit.icon),
                )
        self.unit_markers_node = node

    def _draw_city_nameplate(self) -> None:
        """Generate a billboarding nameplate for the city on this tile."""
        if not self.tile.city:
            return
        atlas = self.icon_atlas
        left = AssetManager.load_pil_image(str(atlas.get_real_path_for_virtual_path("city_plate_left.png")))
        mid = AssetManager.load_pil_image(str(atlas.get_real_path_for_virtual_path("city_plate_middle.png")))
        right = AssetManager.load_pil_image(str(atlas.get_real_path_for_virtual_path("city_plate_right.png")))
        font = AssetManager.load_pil_font("assets/fonts/Washington.ttf", size=224)

        plate = generate_city_nameplate(
            left,
            mid,
            right,
            str(self.tile.city.name),
            self.tile.city.is_capital,
            font=font,
            padding=(20, 8),
            text_offset_y=32,
            star_img=atlas.get_pil_image_by_virtual_path("capital_icon.png"),
            star_offset_y=32,
            star_offset_x=-16,
            text_color=normalize_color_to_bytes(self.tile.owner.color),  # type: ignore[call-arg]
        )
        plate = plate.transpose(
            Image.FLIP_TOP_BOTTOM  # type: ignore[no-untyped-call]
        )  # Flip for Panda3D's coordinate system # type: ignore[no-untyped-call]
        tex = pil_image_to_panda3d_texture(plate)

        cm = CardMaker(f"city_nameplate_{self.tile.id}")
        ar = plate.width / plate.height
        w = 2.5
        h = w / ar
        cm.setFrame(-w / 2, w / 2, -h / 2, h / 2)
        node = self.ui_node.attachNewNode(cm.generate())
        node.setTexture(tex)
        node.setTransparency(TransparencyAttrib.M_alpha)
        node.setBillboardPointEye()
        node.setPos(0, 0, 2.0)
        node.setScale(0.75)
        node.setBin("fixed", 50)
        node.setTwoSided(True)
        node.setAntialias(AntialiasAttrib.MAuto)
        self.city_nameplate_node = node

    def add_model(
        self,
        model_path: str,
        net_type: NET_TYPE,
        pos_offset: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        scale: float = 1.0,
        hpr: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        net_id: Optional[str] = None,
    ) -> None:
        """
        Asynchronously load a model and attach it under geometry_node.
        """
        full_path = str(Path(self.base.get_base_path()).joinpath(model_path).absolute())

        def on_model_loaded(loaded_model: Optional[NodePath]):
            if loaded_model is None:
                self.tile.logger.error(f"Model {full_path} failed to load.")
                return
            x = self.tile.pos_x + pos_offset[0]
            y = self.tile.pos_y + pos_offset[1]
            z = self.tile.pos_z + pos_offset[2]

            loaded_model.setScale(max(0.01, scale))
            loaded_model.setHpr(*hpr)

            node = loaded_model.instanceTo(self.geometry_node)
            node.reparentTo(self.base.render)
            node.setPos(x, y, z)
            node.setCollideMask(BitMask32.bit(1))
            node.setTag(NET_TYPE_FIELD, str(net_type.value))

            if net_id is not None:
                node.setTag(NET_NODE_TAG_ID_FIELD, net_id)
            else:
                node.setTag(NET_NODE_TAG_ID_FIELD, self.tile.tag)

            self.models.append(node)

            if Debug.world_spawning():
                self.tile.logger.debug(
                    f"Added model {model_path} to tile {self.tile.tag} at ({x},{y},{z}) scale {scale}."
                )

        self.base.loader.loadModel(full_path, callback=on_model_loaded)  # type: ignore

    def remove_model(self, net_id: str) -> None:
        """
        Remove any model under geometry_node with NET_NODE_TAG_ID_FIELD == net_id.
        """
        # iterate over a copy, since we may be mutating children
        for model in self.models[:]:
            model.removeNode()
