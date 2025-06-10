from copy import deepcopy
from enum import Enum
from logging import Logger
import math
from pathlib import Path
import random
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Set, Tuple, Type, Union, cast
import weakref


from gameplay.bits import Bit
from gameplay.resources.core.basic._base import BasicBaseResource
from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.resources.core.luxury.luxury_resource import BaseLuxuryResource
from gameplay.resources.core.strategic.strategic_resource import BaseStrategicResource
from helpers.colors import Colors, Tuple4f
from direct.showbase import MessengerGlobal
from direct.showbase.MessengerGlobal import messenger
from panda3d.core import (
    AntialiasAttrib,
    BitMask32,
    CardMaker,
    ColorBlendAttrib,
    LRGBColor,
    NodePath,
    PTAFloat,
    SamplerState,
    Shader,
    Texture,
    TransparencyAttrib,
)

from gameplay._units import Units
from gameplay.combat.damage import DamageMode
from gameplay.condition import Conditions
from gameplay.improvements_set import ImprovementsSet
from gameplay.repositories.tile import TileRepository
from gameplay.resource import BaseResource, Resources
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.unit_icons import UnitIcons
from gameplay.weather import BaseWeather
from gameplay.yields import Yields
from helpers.cache import Cache
from helpers.debug import Debug
from helpers.images import normalize_color_to_bytes
from helpers.maths import scale_value, scaled_pos_z
from helpers.model import ModelHelper
from managers.entity import EntityManager, EntityType
from managers.game import Game
from managers.i18n import T_TranslationOrStr, t_
from managers.input import NET_NODE_TAG_ID_FIELD, NET_TYPE, NET_TYPE_FIELD
from managers.player import PlayerManager
from system.atlas import AtlasGenerator
from system.effects import Effects
from system.entity import BaseEntity
from system.mesh import HexGrid
from system.subsystems.hexgen.enums import GeoformType
from system.subsystems.hexgen.edge import Edge
from world.items._base_item import BaseItem

if TYPE_CHECKING:
    from gameplay.city import City
    from gameplay.improvement import Improvement
    from gameplay.unit import Unit
    from managers.player import Player


class CantBuildReason(Enum):
    COULD_BUILD = 0
    NO_TECH = 1
    NO_RESOURCE = 2
    NOT_PLACEABLE_UPON_TILES = 3  # This is an error in the code, PLACEABLE_ON_TILES should be true if this is the case.
    NOT_PLACEABLE_UPON_CITY = 4
    NOT_PLACEABLE_UPON_CONDITION = 5
    NOT_PLACEABLE_BY_PLAYER = 6
    NOT_PLACEABLE_ON_ENEMY_TILE = 7
    NOT_CONSTRUCTABLE_BUILDER = 8
    IMPROVEMENT_ALREADY_EXISTS = 9
    IMPROVEMENT_TILE_NOT_PASSABLE = 10


class Tile(BaseEntity):
    texture_cache: Dict[str, Texture] = {}
    prop_size_scale_factor: float = 0.3
    prop_slots: Dict[str, Tuple[float, float, float]] = {
        "e": (0.45, 0.0, prop_size_scale_factor),
        "ne": (0.375, 0.35, prop_size_scale_factor),
        "nw": (-0.375, 0.35, prop_size_scale_factor),
        "w": (-0.45, 0.0, prop_size_scale_factor),
        "sw": (-0.375, -0.35, prop_size_scale_factor),
        "se": (0.375, -0.35, prop_size_scale_factor),
        "center": (0.0, 0.0, prop_size_scale_factor),
        "n": (0.0, 0.45, prop_size_scale_factor),
        "s": (0.0, -0.45, prop_size_scale_factor),
    }

    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        pos_x: float = 0.0,
        pos_y: float = 0.0,
        pos_z: float = 0.0,
    ) -> None:
        self.id: int = id(self)
        self.x: int = x
        self.y: int = y
        super().__init__(tile=weakref.ref(self))
        self.tag = self.generate_tag()
        self.pos_x: float = pos_x
        self.pos_y: float = pos_y
        self.pos_z: float = pos_z
        self.z_scale: float = 1.75

        self.hpr: Tuple[float, float, float] = (0.0, 0.0, 0.0)

        self._entity_manager = EntityManager.get_singleton_instance()
        self.logger: Logger = self.base.logger.gameplay.getChild("map.tile")

        self.destroyed: bool = False
        self.grid_position: Optional[Any] = None
        self.raw_position: Optional[Any] = None

        self.models: List[NodePath] = []

        self.is_coast: bool = False
        self.is_water: bool = False
        self.is_land: bool = False
        self.is_sea: bool = False
        self.is_lake: bool = False

        self.edges: Dict[str, Union["Edge", None, weakref.ReferenceType["Edge"]]] = {
            "e": None,
            "ne": None,
            "nw": None,
            "w": None,
            "sw": None,
            "se": None,
        }

        self.is_selected: bool = False

        self.altitude: float = 1
        self.biome: int = 1
        self.moisture: float = 0.0
        self.temperature: float = 1
        self.terrain: str = "plains"
        self.zone: str = "temperate"
        self.hemisphere: str = "north"

        self.resource: Optional[Dict[str, Any]] = None
        self.resources: Resources = Resources()
        self.gameplay_height: int = 0

        self.player: Optional["Player"] = None  # None is nature.

        self.damagable: bool = False
        self.damage: int = 0

        self.damage_per_turn_mode: int = DamageMode.DAMAGE_NONE
        self.damage_per_turn: float = 0.0

        self.damage_per_turn_on_units_mode: int = DamageMode.DAMAGE_NONE
        self.damage_per_turn_on_units: float = 0.0

        self.damage_per_turn_on_improvements_mode: int = DamageMode.DAMAGE_NONE
        self.damage_per_turn_on_improvements: float = 0.0

        self.walkable: bool = True
        self.sailable: bool = False
        self.deep: bool = False
        self.flyable: bool = True
        self.space_above: bool = True

        self.buidable: bool = True
        self.climbable: bool = True
        self.claimable: bool = True

        self.movement_cost: float = 1.0

        self.weather: Optional[BaseWeather] = None

        self.features: Set[Any] = set()
        self.geoforms: Optional[GeoformType] = None
        self.units: Units = Units()
        self._improvements: ImprovementsSet = ImprovementsSet()
        self.items: List[BaseItem] = list()
        self.states: List[Any] = []

        self.city: Optional["City"] = None
        self.city_owner: Optional["City"] = None

        self.owner: Optional["Player"] = None
        self.claimants: List[Any] = []

        self.city_name_group: Optional[NodePath] = None
        self.city_name_texture_card_texture: Optional[NodePath] = None

        self.inherit_passability_from_terrain: bool = True

        self.coast_directions: List[Tuple[int, int]] = []

        self.tile_yield: Yields = Yields(
            gold=0.0,
            production=1.0,
            science=0.0,
            food=1.0,
            culture=0.0,
            housing=0.0,
            mode=Yields.BASE,
        )
        self.meshCollider: bool = True

        self._showing_large_icons: bool = False

        self.effects: Effects = Effects(self)
        self.needs_tile_proecessing: bool = False

        self.tile_icon_group: Optional[NodePath] = None
        self.text_card: Optional[NodePath] = None
        self.icon_overlay_card: Optional[NodePath] = None
        self.icon_overlay: Optional[NodePath] = None
        self.shader: Optional[Shader] = None
        self.atlas: Optional[AtlasGenerator] = None
        self.atlas_width: Optional[int] = None
        self.atlas_height: Optional[int] = None
        self._unit_icons: Optional[UnitIcons] = None

        # 1) one master pivot for positioning/scaling
        self.anchor_node: NodePath = NodePath(f"tile_{x}_{y}")
        self.anchor_node.reparentTo(self.base.render)

        self.geom_group: NodePath = self.anchor_node.attachNewNode("geom_group")
        self.geom_group.set_tag(NET_TYPE_FIELD, str(NET_TYPE.GEOM.value))
        self.geom_group.set_tag(NET_NODE_TAG_ID_FIELD, self.tag)

        self.ui_group: NodePath = self.anchor_node.attachNewNode("ui_group")

        self.anchor_node.setCollideMask(BitMask32.bit(1))
        self.anchor_node.set_tag(NET_TYPE_FIELD, str(NET_TYPE.ANCHOR.value))
        self.anchor_node.set_tag(NET_NODE_TAG_ID_FIELD, self.tag)

        self.hex_overlay_np: Optional[NodePath] = None
        self.visible_sides: Dict[int, bool] = {0: True, 1: True, 2: True, 3: True, 4: True, 5: True}

        self._geom_flattened: bool = False

        self.icon_overlay_np: Optional[NodePath] = None
        self.city_name_np: Optional[NodePath] = None
        self.unit_icons_np: Optional[NodePath] = None
        self._unit_icons: Optional[UnitIcons] = None
        self.model_nodes_by_net_type: Dict[str, List[NodePath]] = {}
        self.placed_props: Dict[str, NodePath] = {}

        self._block_resource_model_spawning: bool = False

        self.atlas = Cache.get_icon_atlas()

    @property
    def tile_terrain(self) -> BaseTerrain:
        return self._tile_terrain

    @tile_terrain.setter
    def tile_terrain(self, value: BaseTerrain) -> None:
        self._tile_terrain = value
        if self.inherit_passability_from_terrain:
            self.passable: bool = True if self.tile_terrain.passable is True else False
            self.passable_without_tech: bool = True if self.tile_terrain.passable_without_tech is True else False

    def get_tile_terrain(self) -> BaseTerrain:
        return self._tile_terrain

    def get_edge(self, side: str) -> Optional["Edge"]:
        if side not in self.edges:
            raise ValueError(f"Invalid edge side: {side}. Valid sides are: {list(self.edges.keys())}")
        edge = self.edges[side]
        if isinstance(edge, weakref.ReferenceType):
            return edge()
        return edge

    def get_edges(self, as_reference: bool = True) -> Dict[str, Union["Edge", None, weakref.ReferenceType["Edge"]]]:
        data: Dict[str, Union[weakref.ReferenceType["Edge"], "Edge", None]] = {}
        for side, edge in self.edges.items():
            if isinstance(edge, weakref.ReferenceType) and not as_reference:
                edge = edge()
            elif isinstance(edge, Edge) and as_reference:
                edge = weakref.ref(edge)
            data[side] = edge
        return data

    def flatten(self):
        for model in self.models:
            model.flattenStrong()

    def generate_tag(self) -> str:
        return f"tile_{self.x}_{self.y}"

    def on_load(self) -> None:
        self.models = []
        self.base = Cache.get_showbase_instance()
        self.logger = self.base.logger.gameplay.getChild("map.tile")

        # self._render_default_terrain()
        # self.create_root_ui_node()

        if self.tile_icon_group is None:
            raise AssertionError("Tile icon group not created.")

        self.text_card = NodePath("text_card")
        self.text_card.reparentTo(self.tile_icon_group)  # type: ignore

        self.render()

        if self.city is not None:
            self.city.base = self.base
            self.city.register()

    def calculate(self):
        base = deepcopy(self._tile_terrain.get_tile_yield())  # This is to prevent modifying the base yield.

        for improvement in self._improvements.get_all():
            base += improvement.tile_yield

        for effect in self.effects.get_effects().values():
            base += effect.yield_impact

        self.tile_yield = base

    def __getstate__(self) -> Dict[str, Any]:
        state = self.__dict__.copy()
        if "base" in state:
            del state["base"]
        if "logger" in state:
            del state["logger"]
        if "texture_card" in state:
            del state["texture_card"]
        if "texture_card_texture" in state:
            del state["texture_card_texture"]
        if "city_name_group" in state:
            del state["city_name_group"]
        if "city_name_texture_card_texture" in state:
            del state["city_name_texture_card_texture"]
        if "tile_icon_group" in state:
            del state["tile_icon_group"]
        if "text_card" in state:
            del state["text_card"]
        if "_model" in state:
            del state["_model"]
        if "_entity_manager" in state:
            del state["_entity_manager"]
        if "models" in state:
            del state["models"]
        return state

    def set_visible_sides(self, sides: Dict[int, bool]) -> None:
        if len(sides) != 6:
            raise ValueError("visible_sides must be a list of length 6.")
        self.visible_sides = sides.copy()

    def is_side_visible(self, side_index: int) -> bool:
        return self.visible_sides[side_index]

    def get_visible_sides(self) -> List[int]:
        return [i for i, v in enumerate(self.visible_sides) if v]

    def get_pos(self) -> Tuple[float, float, float]:
        return self.pos_x, self.pos_y, self.pos_z

    def __repr__(self) -> str:
        return f"{self.id}@{self.x},{self.y}"

    def is_resource_improved(self) -> bool | None:
        resources = self.resources.flatten()
        if len(resources) == 0:
            return None

        for resource in resources.values():
            if resource.improvement_required is not None:
                for improvement in self._improvements.get_all():
                    if resource.improvement_required == improvement.__class__ or (
                        isinstance(resource.improvement_required, list)
                        and improvement.__class__ in resource.improvement_required
                    ):
                        return True
        return False

    def get_improved_resources(self) -> List[BaseResource]:
        resources = self.resources.flatten()
        if len(resources) == 0:
            return []

        improved_resources: List[BaseResource] = []
        for resource in resources.values():
            if resource.improvement_required is not None:
                for improvement in self._improvements.get_all():
                    if resource.improvement_required == improvement.__class__ or (
                        isinstance(resource.improvement_required, list)
                        and improvement.__class__ in resource.improvement_required
                    ):
                        improved_resources.append(resource)
        return improved_resources

    def register(self):
        from managers.entity import EntityType  # Prevent circular import

        self._entity_manager.register(entity=self, key=str(self.id), type=EntityType.TILE)

    def select(self) -> None:
        self.is_selected = True
        self.on_select()

    def deselect(self) -> None:
        self.is_selected = False
        self.on_deselect()

    def on_select(self) -> None: ...

    def on_deselect(self) -> None: ...

    def unregister(self):
        from managers.entity import EntityType  # Prevent circular import

        self._entity_manager.unregister(entity=self, type=EntityType.TILE)

    def compute_hex_center(self, x: int, y: int, radius: float = 1) -> Tuple[float, float]:
        # same as get_hex_spacing
        horizontal_spacing = 1.5 * radius
        vert = math.sqrt(3) * radius

        # column offset in X
        pos_x = x * horizontal_spacing
        pos_y = y * vert + (vert * 0.5 if (x % 2) else 0.0)

        return pos_x, pos_y

    def is_visisted_by(self, unit: "Unit") -> bool:
        messenger.send("unit.action.move.visiting_tile", [unit, self])
        self.logger.info(f"Unit {str(unit.tag)} is visiting tile {str(self.tag)}.")
        return True

    def add_city_name(self) -> None:
        if self.city is None:
            return

        from PIL import Image  # Needed for flip

        from helpers.images import generate_city_nameplate, pil_image_to_panda3d_texture
        from managers.assets import AssetManager

        atlas = Cache.get_icon_atlas()

        # Load the assets
        left_img = AssetManager.load_pil_image(str(atlas.get_real_path_for_virtual_path("city_plate_left.png")))
        middle_img = AssetManager.load_pil_image(str(atlas.get_real_path_for_virtual_path("city_plate_middle.png")))
        right_img = AssetManager.load_pil_image(str(atlas.get_real_path_for_virtual_path("city_plate_right.png")))
        font = AssetManager.load_pil_font("assets/fonts/Washington.ttf", size=224)

        if not (left_img and middle_img and right_img and font):
            raise RuntimeError("Failed to load nameplate assets.")

        # Generate the PIL nameplate
        pil_nameplate = generate_city_nameplate(
            left_img,
            middle_img,
            right_img,
            str(self.city.name),
            self.city.is_capital,
            font=font,
            padding=(20, 8),  # horizontal/vertical padding
            text_offset_y=32,
            star_img=atlas.get_pil_image_by_virtual_path("capital_icon.png"),
            star_offset_y=32,
            star_offset_x=-16,
            text_color=normalize_color_to_bytes(self.owner.color) if self.owner else (255, 0, 0, 255),  # type: ignore
        )

        # --- Stretch PIL canvas to force slim aspect ratio ---
        forced_aspect_ratio = 1.5
        width = pil_nameplate.width
        desired_width = int(pil_nameplate.height * forced_aspect_ratio)

        if width < desired_width:
            new_img = Image.new("RGBA", (desired_width, pil_nameplate.height), (0, 0, 0, 0))
            x_offset = (desired_width - width) // 2
            new_img.paste(pil_nameplate, (x_offset, 0))
            pil_nameplate = new_img

        # --- Fix upside down issue ---
        pil_nameplate = pil_nameplate.transpose(Image.FLIP_TOP_BOTTOM)  # type: ignore

        # Convert to Panda3D texture
        city_texture = pil_image_to_panda3d_texture(pil_nameplate)

        # Build the city name card
        card_maker = CardMaker(f"city_nameplate_{self.id}")
        aspect_ratio = pil_nameplate.width / pil_nameplate.height
        card_width = 2.5  # wider
        card_height = card_width / aspect_ratio
        card_maker.setFrame(-card_width / 2, card_width / 2, -card_height / 2, card_height / 2)

        city_np = self.ui_group.attachNewNode(card_maker.generate())  # type: ignore
        city_np.setTexture(city_texture)
        city_np.setTransparency(TransparencyAttrib.MAlpha)
        city_np.setColor(1, 1, 1, 1)
        city_np.clearColorScale()
        # Proper orientation
        city_np.setHpr(0, 0, 0)
        city_np.setBillboardPointEye()
        city_np.setPos(0, 0, 2.0)
        city_np.setScale(0.75)

        city_np.setBin("fixed", 50)
        city_np.setDepthWrite(True)
        city_np.setDepthTest(True)
        city_np.setTwoSided(True)
        city_np.setAntialias(AntialiasAttrib.MAuto)

        if self.models:
            city_np.reparentTo(self.base.render)

    def get_atlas(self) -> AtlasGenerator:
        if self.atlas is None:
            self.atlas = Cache.get_icon_atlas()
        return self.atlas

    def add_icon_to_tile(self) -> None:
        """Create the resource-icon overlay once, then just update its UVs each frame."""
        # build the card on first call
        cm = CardMaker(f"icon_overlay_{self.id}")
        cm.setFrame(-1, 1, -1, 1)
        cm.setHasUvs(True)

        if self.icon_overlay_np is not None:
            self.icon_overlay_np.remove_node()
            self.icon_overlay_np = None

        self.icon_overlay_np = self.ui_group.attachNewNode(cm.generate())
        self.icon_overlay_np.setPos(0, 0, 0)
        self.icon_overlay_np.setCollideMask(BitMask32.bit(1))
        self.icon_overlay_np.setTransparency(TransparencyAttrib.MAlpha)
        self.icon_overlay_np.setAttrib(ColorBlendAttrib.makeOff())
        self.icon_overlay_np.setBin("fixed", 60)
        self.icon_overlay_np.setDepthTest(True)
        self.icon_overlay_np.setDepthWrite(False)
        self.icon_overlay_np.setHpr(0, -90, 0)
        self.icon_overlay_np.setScale(0.75)

        self.icon_overlay_np.set_tag("net_type", NET_TYPE.TILE.value)
        self.icon_overlay_np.set_tag("net_node_tag_id", self.tag)

        self.icon_overlay_np.setShader(
            Shader.load(
                Shader.SL_GLSL, "assets/shaders/resource_icons.vert.glsl", "assets/shaders/resource_icons.frag.glsl"
            )
        )
        # load atlas once
        atlas = Cache.get_icon_atlas()
        atlas_tex = atlas.get_panda3d_texture()
        atlas_tex.setWrapU(Texture.WMClamp)
        atlas_tex.setWrapV(Texture.WMClamp)
        atlas_tex.setFormat(Texture.F_srgb_alpha)
        atlas_tex.setMinfilter(SamplerState.FT_linear)
        atlas_tex.setMagfilter(SamplerState.FT_linear)
        atlas_tex.setAnisotropicDegree(0)
        self.icon_overlay_np.setShaderInput("icon_atlas", atlas_tex)  # type: ignore[union-attr]

        self.atlas_width, self.atlas_height = atlas.atlas_image.size

        # compute which icons to show
        resources: List[BaseResource] = list(self.resources.flatten().values())
        basic = self.get_tile_yield()
        if self.city:
            basic += self.city.get_yield()
        slots: List[Optional[Union[str, BaseResource]]] = [None] * 7
        if self.city:
            slots[0] = self.city.get_population_icon()
        elif resources:
            slots[0] = resources[0]
        for i, resource in enumerate(basic.export_basic()):
            slots[i + 1] = resource

        # fill the UV array
        uv = PTAFloat.emptyArray(4 * 7)
        for i, resource in enumerate(slots):
            if not resource:
                continue

            def get_resource_path(resource: Union[str, BaseResource]) -> str | None:
                if isinstance(resource, str):
                    return resource.replace("resources/", "")
                elif isinstance(resource, (BaseBonusResource, BaseLuxuryResource, BaseStrategicResource)):
                    return resource.icon.replace("assets/icons", "")
                elif isinstance(resource, BasicBaseResource):
                    if resource.value > 0:
                        return resource.get_numeric_icon().replace("resources/", "")
                    return resource.icon
                return None

            path: str | None = None
            if i == 0:
                if self.city is not None:
                    path = self.city.get_population_icon().replace("resources/", "")
                else:
                    path = resources[0].icon.replace("assets/icons/", "")
            else:
                if isinstance(resource, BaseResource) and resource.value == 0:
                    continue

                path = get_resource_path(resource)

            if path is None:
                continue

            pos = self.get_atlas().get_position_for_virtual_path(path)
            size = self.get_atlas().get_dimensions_for_virtual_path(path) if pos else None

            if not pos or not size:
                raise AssertionError(f"Icon not found in atlas: {path}")

            x, y = pos
            w, h = size
            u0, v1 = x / self.atlas_width, 1.0 - (y / self.atlas_height)
            u1, v0 = (x + w) / self.atlas_width, 1.0 - ((y + h) / self.atlas_height)
            base = i * 4
            uv[base + 0], uv[base + 1], uv[base + 2], uv[base + 3] = u0, v0, u1, v1

        # push UVs & count into the shader
        self.icon_overlay_np.setShaderInput("uv_rects", uv)  # type: ignore[union-attr]
        self.icon_overlay_np.setShaderInput("icon_count", 7)  # type: ignore[union-attr]
        # ensure it stays at the right Z offset
        self.icon_overlay_np.setZ(0 + 0.01)

    def get_distance(self, other: "Tile") -> int:
        return TileRepository.distance(self, other)

    def recalculate_grid_position(self, radius: float = 1) -> None:
        """
        Recompute self.pos_x/pos_y from self.x,self.y & radius
        so it matches the mesh layout exactly.
        """
        px, py = self.compute_hex_center(self.x, self.y, radius)
        self.pos_x, self.pos_y = px, py

    def set_walls_color(self, color: Tuple[float, ...]) -> None:
        mesh: HexGrid = Game.get_singleton_instance().get_mesh()
        mesh.set_wall_color_for_tile(mesh.get_tile_index_from_coords(self.x, self.y), cast(Tuple4f, color))

    def render(self, auto_calculate: bool = True) -> None:
        from panda3d.core import CardMaker

        if auto_calculate:
            self.calculate()

        self.anchor_node.setPos(self.pos_x, self.pos_y, 0)
        self.anchor_node.setScale(1)

        cm = CardMaker(f"hex_overlay_{self.id}")
        overlay_size = 1.0  # Adjust this to fit your tile, must fully cover hex
        cm.setFrame(-overlay_size, overlay_size, -overlay_size, overlay_size)

        if self.hex_overlay_np is not None:
            self.hex_overlay_np.remove_node()
            self.hex_overlay_np = None

        self.hex_overlay_np = self.ui_group.attachNewNode(cm.generate())
        self.hex_overlay_np.setTransparency(1)
        self.hex_overlay_np.setAttrib(ColorBlendAttrib.makeOff())
        self.hex_overlay_np.setBin("fixed", 40)  # Drawn below icons, above terrain
        self.hex_overlay_np.setDepthTest(True)
        self.hex_overlay_np.setDepthWrite(False)
        self.hex_overlay_np.setHpr(0, -90, 0)  # Flat on X/Y plane
        self.hex_overlay_np.setScale(1.0)
        self.hex_overlay_np.setPos(0, 0, 0.001)  # Just above terrain, below icons

        # Load the overlay texture (alpha hex in square PNG)
        texture_name: Optional[str] = None
        if hasattr(self.get_terrain(), "texture"):
            texture_name = str(self.tile_terrain.texture())
        elif hasattr(self.get_terrain(), "name"):
            texture_name = getattr(self.get_terrain(), f"{self.name}.png", "default.png")

        if texture_name is None or texture_name == "":
            texture_name = "default.png"

        atlas = Cache.get_terrain_atlas()

        for improvement in self._improvements.get_all():
            if improvement.model is not None:
                self.add_model(improvement.model, net_type=NET_TYPE.IMPROVEMENT)

        self.unrender_bits()
        self.render_bits()
        self.render_resource_model()

        self.add_icon_to_tile()
        self.add_unit_icon()

        if self.units.has_any():
            for unit in self.units.all():
                unit.render()  # We let the unit handle its own rendering.

        if self.city is not None:
            self.add_city_name()

        texture: Optional[Texture] = atlas.get_panda3d_texture_by_virtual_path(texture_name)
        if texture is None:
            raise AssertionError(f"Texture not found: {texture_name}")

        self.hex_overlay_np.setTexture(texture, 1)
        self.set_walls_color(Colors.to_normalized_float(self.get_terrain().wall_color(), 1.0))

        if not self._geom_flattened:
            self.geom_group.flatten_medium()
            self._geom_flattened = True

        # lift all UI elements together
        self.ui_group.setZ(self.pos_z + 0.01)

    def render_bits(self):
        self.unrender_bits()
        for bit in self.get_terrain().get_bits():
            if bit.blocks_resource_model_spawning is True:
                self._block_resource_model_spawning = True
            self.render_bit_into_slot(bit, None)

    def search_bit(self, bit_id: str) -> Optional["Bit"]:
        if (bit := self.get_terrain().bits.search_bit(bit_id)) is not None:
            return bit
        return None

    def enable_bit(self, bit: "Bit", slot: Optional[str] = None) -> None:
        bit.disabled = False

        if bit.has_preferred_slot():
            slot_name = bit.get_preferred_slot_name() or slot

            if slot_name is None or slot_name not in self.prop_slots:
                raise ValueError(f"Slot {slot_name} not found in prop slots: {self.prop_slots.keys()}")

            if not self.if_pop_slot_available(slot_name):
                return
        else:
            slot_name = None
        model = self.render_bit_into_slot(bit, slot_name)
        if model is None:
            raise ValueError(f"Could not render bit {bit} into slot {slot_name}. Slot may not be available.")

    def disable_bit(self, bit: "Bit") -> None:
        bit.disabled = True
        self.model_nodes_by_net_type[str(NET_TYPE.BIT.value)] = [
            model
            for model in self.model_nodes_by_net_type.get(str(NET_TYPE.BIT.value), [])
            if model.get_tag(NET_NODE_TAG_ID_FIELD) != bit.id
        ]

    def render_bit_into_slot(
        self,
        bit: "Bit",
        slot_name: Optional[str] = None,
    ) -> Optional[NodePath]:
        slots = ModelHelper.calculate_hex_slot_positions() if self.prop_slots == {} else self.prop_slots
        model = ModelHelper.load_model(bit.model)
        if bit.is_disabled():
            return None

        if bit.has_preferred_slot():
            slot_name = bit.get_preferred_slot_name()
            if slot_name is None or slot_name not in slots:
                raise ValueError(f"Slot {slot_name} not found in prop slots: {slots.keys()}")
            if not self.if_pop_slot_available(slot_name):
                return None

        elif slot_name is None:
            shuffled_slots = list(slots.keys())
            random.shuffle(shuffled_slots)
            for slot in shuffled_slots:
                if self.if_pop_slot_available(slot):
                    slot_name = slot
                    break

            if slot_name is None:
                return None

        pos_offset = (bit.offset[0] + slots[slot_name][0], bit.offset[1] + slots[slot_name][1], bit.offset[2])
        slot_position = slots[slot_name]
        scale = (
            ModelHelper.calculate_slot_scale_factor(model, slot_positions=slot_position)
            if bit.allow_auto_scale
            else bit.scale
        )

        self.add_model(
            model_path=bit.model,
            pos_offset=pos_offset,
            scale=scale,
            hpr=bit.hpr,
            net_type=NET_TYPE.BIT,
            net_id=bit.id,
        )
        self.placed_props[slot_name] = model

        return model

    def unrender_bit_slot(self, slot_name: str) -> None:
        if slot_name not in self.placed_props:
            raise ValueError(f"Slot {slot_name} not found in placed props: {self.placed_props.keys()}")

        model = self.placed_props.pop(slot_name)
        self.models.remove(model)
        model.removeNode()

        # Remove from model_nodes_by_net_type
        if str(NET_TYPE.BIT.value) in self.model_nodes_by_net_type:
            self.model_nodes_by_net_type[str(NET_TYPE.BIT.value)].remove(model)

        self.geom_group.flattenMedium()

    def if_pop_slot_available(self, slot_name: str) -> bool:
        """
        Check if a prop slot is available for rendering.
        """
        if slot_name not in self.prop_slots:
            raise ValueError(f"Slot {slot_name} not found in prop slots: {','.join(list(self.prop_slots.keys()))}")
        return slot_name not in self.placed_props

    def unrender_bits(self) -> None:
        """
        Remove all bit models from the tile.
        """
        try:
            for model in self.model_nodes_by_net_type[str(NET_TYPE.BIT.value)]:
                try:
                    self.models.remove(model)
                except ValueError:
                    continue
                model.removeNode()
            self.placed_props.clear()
        except KeyError:
            return None
        self._block_resource_model_spawning = False
        self.geom_group.flattenMedium()

    def remove_unit_icons(self) -> None:
        if self._unit_icons is not None:
            self._unit_icons.remove_all()
            if self.unit_icons_np is not None:
                self.unit_icons_np.removeNode()
            self.unit_icons_np = None
            self._unit_icons = None
        else:
            self.logger.warning("No unit icons to remove.")

    def add_unit_icon(self) -> None:
        if self.unit_icons_np is not None:
            self.unit_icons_np.remove_node()

        self.unit_icons_np = self.ui_group.attachNewNode("unit_icons")
        # Initialize the UnitIcons helper once
        self._unit_icons = UnitIcons(self.unit_icons_np)

        self._unit_icons.remove_all()

        # Compute world‐space base position of this tile
        x, y, z = self.anchor_node.getPos(self.base.render)  # type: ignore[name-defined]

        # Add a marker for each unit
        for unit in self.units.all():
            if unit.icon:
                # Place each icon slightly above the tile
                self._unit_icons.add_marker(
                    (x, y, z + 1.5),  # position
                    (0.2, 0.2),  # size
                    str(unit.icon),  # icon name/tag
                )

    def render_resource_model(self) -> None:
        if self.city is not None or self._block_resource_model_spawning:
            return

        resource = list(self.resources.flatten_non_mechanic().values())

        if len(resource) == 0:
            return

        resource = resource[0]

        if resource.model is None or (isinstance(resource.model, tuple) and resource.model == (None, None)):
            return

        if (model := (resource.get_land_model() if self.is_land else resource.get_water_model())) is None:
            return

        self.add_model(
            model_path=model,
            pos_offset=resource.model_position,
            scale=resource.model_size,
            hpr=resource.model_hpr,
            net_type=NET_TYPE.RESOURCE,
        )

    def on_turn_end(self, turn: int) -> None:
        """Will only be called by the world manager. when the tile has an effect, unit, city or player."""
        if len(self._improvements) > 0:  # We only process improvements if we have any.
            self._improvements.on_turn_end(turn)

        if len(self.effects) > 0:
            self.effects.on_turn_end(turn)

        if len(self.units) > 0:
            for unit in self.units.all():
                unit.attack_points_left = unit.attack_points  # Reset attack points for the next turn

    def calculate_z_pos_on_altitude(self) -> Tuple[float, float, float]:
        pos_z = scale_value(min(self.altitude, 240), 44, 240, 0, 1.5)
        pos_z = scaled_pos_z(pos_z, -0.25, 0.75, self.z_scale)
        return (self.pos_x, self.pos_y, float(pos_z))

    def _render_improvements(self) -> None:
        improvements: List[Improvement] = self.improvements().get_all()
        for improvement in improvements:
            model_path = improvement.get_model_path()

            if model_path is None:
                continue

            self.add_model(
                model_path=model_path,
                pos_offset=improvement.get_model_offset(),  # type: ignore
                scale=improvement.get_model_scale(),  # type: ignore
                hpr=improvement.get_model_hpr(),  # type: ignore,
                net_type=NET_TYPE.IMPROVEMENT,
            )

    def add_model(
        self,
        model_path: str,
        net_type: NET_TYPE,
        pos_offset: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        scale: float = 0.41,
        hpr: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        net_id: Optional[str] = None,
    ) -> None:
        """
        Asynchronously load and add an additional model on top of the tile.
        """
        base_path: Path = self.base.get_base_path()
        full_path = str(base_path.joinpath(model_path).absolute())

        def on_model_loaded(extra_model: Optional[NodePath], net_type: NET_TYPE) -> None:
            if extra_model is None:
                self.logger.error(f"Model {full_path} failed to load.")
                return

            x = self.pos_x + pos_offset[0]
            y = self.pos_y + pos_offset[1]
            z = self.pos_z + pos_offset[2]

            model_scale = max(0.01, scale)
            extra_model.setScale(model_scale)
            extra_model.setHpr(*hpr)

            node: NodePath = extra_model.instanceTo(self.geom_group)
            node.reparentTo(self.base.render)
            node.setPos(x, y, z)
            node.setCollideMask(BitMask32.bit(1))

            self.models.append(node)
            self.model_nodes_by_net_type.setdefault(str(net_type.value), []).append(node)
            node.setTag(NET_TYPE_FIELD, str(net_type.value))
            node.setTag(NET_NODE_TAG_ID_FIELD, self.tag if (net_id is None) else net_id)

            if Debug.world_spawning():
                self.logger.debug(
                    f"Added model {model_path} to tile {self.tag} at position ({x}, {y}, {z}) with scale {model_scale}."
                )

        self.base.loader.loadModel(full_path, callback=on_model_loaded, extraArgs=[net_type])

    def unrender(self) -> None:
        self.unrender_all()

    def unrender_by_type(self, net_type: NET_TYPE) -> None:
        desired_tag = str(net_type.value)
        to_remove = [
            node
            for node in self.model_nodes_by_net_type.values()
            if isinstance(node, NodePath) and node.getTag(NET_TYPE_FIELD) == desired_tag
        ]

        if not to_remove:
            return

        for node in to_remove:
            try:
                self.models.remove(node)
            except ValueError:
                print(f"  WARNING: Node {node} was not in self.models, skipping remove().")
            node.removeNode()

    def unrender_all(self, icons: bool = False) -> None:
        for node in self.models:
            node.removeNode()
        if self._unit_icons is not None:
            self._unit_icons.remove_all()

        self.models.clear()

    def set_color(self, color: Tuple[float, float, float, float]) -> None:
        for node in self.models:
            node.setColor(*color)

    def get_node(self) -> Optional[NodePath]:
        return self.models[0] if self.models else None

    def get_units(self) -> Units:
        return self.units

    def set_terrain(self, terrain: BaseTerrain) -> None:
        self.tile_terrain = terrain

    def get_terrain(self) -> BaseTerrain:
        return self.tile_terrain

    def get_climbable(self) -> bool:
        return self.climbable

    def is_spawnable_upon(self, on_other_units: bool = False, on_mountains: bool = False) -> bool:
        return (
            not self.is_water
            and not self.is_sea
            and (on_other_units or len(self.units) == 0)
            and not self.city
            and (
                on_mountains or self.altitude < 200
            )  # No spawning on mountains # @TODO this might be a bug. check in the future if this is the reason units can spawn on mountains.
        )

    def is_passable(self) -> bool:
        if self.inherit_passability_from_terrain:
            return self.passable
        return self.walkable and not self.is_water

    def color(self) -> Union[Tuple[float, float, float], LRGBColor]:
        if self.tile_terrain:
            return self.tile_terrain.color()
        else:
            self.logger.error(f"No terrain set for tile, returning default color: {self.__class__.__name__}")
            return (0, 0, 0)

    def model(self) -> str:
        return str(self.tile_terrain.model()) if self.tile_terrain and self.tile_terrain.get_model() is not None else ""

    def texture(self) -> T_TranslationOrStr:
        return self.tile_terrain.texture() if self.tile_terrain else ""

    def addTileYield(self, tileYield: Yields) -> None:
        self.tile_yield.values += tileYield  # type: ignore

    def get_tile_yield(self) -> Yields:
        yield_copy = deepcopy(self.tile_yield)
        for resource in self.resources.flatten().values():
            yield_copy += resource.tile_yield
        for resource in self.get_improved_resources():
            yield_copy += resource.tile_yield_on_improvement
        return yield_copy

    def get_resources(self) -> Resources:
        return self.resources

    def add_resource(self, resource: BaseResource) -> None:
        self.resources.add(resource)

    def remove_resource(self, resource: BaseResource) -> None:
        self.resources.remove(resource)

    def improvements(self) -> ImprovementsSet:
        return self._improvements

    def is_city(self) -> bool:
        return self.city is not None

    def add_unit(self, unit: "Unit") -> None:
        self.units.add_unit(unit)

    def remove_unit(self, unit: "Unit") -> None:
        # Assuming the intent is to remove the unit.
        self.units.remove_unit(unit)

    def is_occupied(self) -> bool:
        return len(self.units._units) > 0 or self.city is not None  # type: ignore

    def to_gui(self) -> Dict[str, Any]:
        terrain_name: T_TranslationOrStr = t_("civilization.nature.name")

        _improvements: List[str] = []
        if self.city is not None:  # We add the city improvements to the list of improvements.
            _improvements += [str(improvement.name) for improvement in self.city.get_improvements()]
        for improvement in self._improvements.get_all():
            _improvements.append(str(improvement.name))

        _units: List[str] = []
        for unit in self.units.all():  # type: ignore
            data = unit.to_gui()
            _units.append(f"{data['tag']} {data['name']}")

        yields = self.get_tile_yield()
        if self.city:
            city_yields = self.city.get_yield()
            yields += city_yields

        data: Dict[str, Any] = {
            "tag": self.tag,
            "x(col), y(row)": f"{self.x}, {self.y}",
            "terrain": terrain_name,
            "altitude": self.altitude,
            "visible_sides": ",".join(map(str, self.visible_sides.values())),
            "model": self.model(),
            "passable": f"{str(self.passable)}, {str(self.passable_without_tech)}",
            "movement_cost": self.movement_cost,
            "texture": self.texture(),
            "class": self.__class__.__name__,
            "owner": str(self.owner.name) if self.owner else str(t_("civilization.nature.name")),
            "owner_city": str(self.city_owner.name) if self.city_owner else str(t_("civilization.nature.name")),
            "city": self.city,
            "improvements": " | ".join(_improvements),
            "tile_yield": str(yields),
            "temperature": self.temperature,
            "resources": self.resources.flatten(),
            "features": self.features,
            "units": ",".join(_units),
            "health": self.health(),
            "damage": self.damage,
            "pos": (self.pos_x, self.pos_y, self.pos_z),
            "effective_z": self.calculate_z_pos_on_altitude(),
            "Hpr": ",".join(map(str, self.hpr)),
            "effects": ",".join(self.effects.get_effects().keys()),
            "resource_improved": "Yes" if self.is_resource_improved() else "No",
            "Is selected": "Yes" if self.is_selected else "No",
        }

        data["hex_data"] = {
            "altitude": self.altitude,
            "biome": f"{self.biome.id} - {self.biome.name}",  # type: ignore
            "moisture": self.moisture,
            r"is_[coast|sea|water|land|lake]": f"{self.is_coast}|{self.is_sea}|{self.is_water}|{self.is_land}|{self.is_lake}",
            "is_city": self.is_city(),
            "terrain": self.terrain,
            "features": ",".join(str(feature) for feature in self.features),
            "geoform": self.geoforms,
            "zone": self.zone,
            "hemisphere": self.hemisphere,
            "resource['rating']": self.resource["rating"] if self.resource else None,
            "resource['type']": self.resource["type"] if self.resource else None,
        }

        data["hex_data"] = "\n".join(f"{k}: {v}" for k, v in data["hex_data"].items())

        if self.city is not None:
            data["city"] = {
                "city_name": self.city.name,
                "owned_tiles": ",".join(str(tile.tag) for tile in self.city.owned_tiles),
                "population": self.city.population,
                "is_capital": self.city.is_capital,
                "is_building": self.city.is_building,
                "building": self.city.building,
                "resources_needed": f"{self.city.resource_required_amount}/{self.city.resource_collected}",
            }
            data["city"] = "\n".join(f"{k}: {v}" for k, v in data["city"].items())

        if self.units.has_any():
            if (unit := self.units.first()) is not None:
                data.update({"unit_stats": unit.to_gui()})

        return data

    def found(
        self,
        player: Optional["Player"] = None,
        population: int = 1,
        capital: Optional[bool] = None,
    ) -> bool:
        from gameplay.city import City
        from gameplay.terrain.city import City as CityTerrain

        if player is None:
            player = PlayerManager.player()

        if capital is None:
            capital = len(player.cities) == 0

        self.city = City.found_new(
            name=player.civilization.get_city_name(),
            owner=player,
            tile=self,
            population=population,
            is_capital=capital,
            auto_claim_radius=1,
        )

        self.owner = player
        self.owner.tiles.add_tile(self)
        self.owner.add_tile(self)

        if self.owner.capital is not None:
            self.owner.capital.de_capitalize()

        self.owner.capital = self.city

        self.set_terrain(CityTerrain())
        self.render()
        MessengerGlobal.messenger.send("game.border.refresh")

        return True

    def build(self, improvement: "Improvement") -> Literal[True] | CantBuildReason:
        if not improvement.placeable_on_tiles:
            return CantBuildReason.NOT_PLACEABLE_UPON_TILES
        if improvement.placeable_on_city is False and self.city is not None:
            return CantBuildReason.NOT_PLACEABLE_UPON_CITY
        if improvement.placeable_on_condition and isinstance(improvement.placeable_on_condition, Conditions):
            condition_check_result: bool = improvement.placeable_on_condition.are_met(
                {"tile": self, "improvement": improvement}
            )
            if condition_check_result is False:
                return CantBuildReason.NOT_PLACEABLE_UPON_CONDITION

        improvement.set_tile(self)
        improvement.on_construct()
        self._improvements.add(improvement)
        self.get_terrain().on_build_upon(improvement)
        self.render()
        return True

    def destroy_improvement(self, improvement: "Improvement") -> None:
        self._improvements.remove(improvement)
        improvement.on_destroy()

    def get_buildable_improvements(self) -> List[Type["Improvement"]]:
        def get_buildable_from_resources() -> List[Type["Improvement"]]:
            buildable_improvements: List[Type["Improvement"]] = []
            for resource in self.resources.flatten().values():
                if resource.improvement_required is not None:
                    improvement_required = (
                        resource.improvement_required
                        if isinstance(resource.improvement_required, list)
                        else [resource.improvement_required]
                    )
                    for improvement in improvement_required:
                        if improvement not in buildable_improvements:
                            buildable_improvements.append(improvement)
            return buildable_improvements

        buildable_improvements: List[Type["Improvement"]] = list(
            set(get_buildable_from_resources() + self.get_terrain().supported_improvements())
        )
        return buildable_improvements

    def get_cords(self) -> Tuple[float, float, float]:
        return self.pos_x, self.pos_y, self.pos_z

    def get_map_cords(self) -> Tuple[int, int]:
        return self.x, self.y

    def instance_resource(self, resource: Type[BaseResource]):
        """Just here to decouplel it from enrich from extra data as it will be gone soon."""
        self.resources.add(resource(3), auto_instance=True)

    def is_showing_large_icons(self) -> bool:
        return self._showing_large_icons

    def destroy(self, as_system: bool = False) -> None:
        self._entity_manager.unregister(entity=self, type=EntityType.TILE)
        self.unrender_all()
        self.destroyed = True
