from copy import deepcopy
from enum import Enum
from logging import Logger
from os.path import dirname, join, realpath
from pathlib import Path
from posixpath import abspath
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Tuple, Type, Union
import weakref

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
)

from gameplay._units import Units
from gameplay.combat.damage import DamageMode
from gameplay.condition import Conditions
from gameplay.improvements_set import ImprovementsSet
from gameplay.resource import BaseResource, Resources
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.weather import BaseWeather
from gameplay.yields import Yields
from helpers.cache import Cache
from helpers.colors import Colors
from helpers.images import normalize_color_to_bytes
from managers.entity import EntityManager, EntityType
from managers.i18n import T_TranslationOrStr, t_
from managers.player import PlayerManager
from system.effects import Effects
from system.entity import BaseEntity
from system.subsystems.hexgen.hex import Hex
from world.features._base_feature import BaseFeature
from world.items._base_item import BaseItem

if TYPE_CHECKING:
    from gameplay.city import City
    from gameplay.improvement import Improvement
    from gameplay.units.unit import Unit
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


class BaseTile(BaseEntity):
    texture_cache: Dict[str, Texture] = {}

    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        pos_x: float = 0.0,
        pos_y: float = 0.0,
        pos_z: float = 0.0,
        extra_data: Optional[Dict[Any, Any]] = None,
    ) -> None:
        self.id: int = id(self)
        self.x: int = x
        self.y: int = y
        super().__init__(tile=weakref.ref(self))
        self.pos_x: float = pos_x
        self.pos_y: float = pos_y
        self.pos_z: float = pos_z
        self.hpr: Tuple[float, float, float] = (0.0, 0.0, 0.0)

        self._entity_manager = EntityManager.get_singleton_instance()
        self.logger: Logger = self.base.logger.gameplay.getChild("map.tile")

        self.destroyed: bool = False
        self.grid_position: Optional[Any] = None
        self.raw_position: Optional[Any] = None
        self.tag: Optional[str] = None
        # Instead of a single node, we keep a list of NodePaths.

        self.models: List[NodePath] = []

        self.is_coast: bool = False
        self.is_water: bool = False
        self.is_land: bool = False
        self.is_sea: bool = False
        self.is_lake: bool = False

        self.altitude: float = 0.0
        self.biome: int = 1
        self.moisture: float = 0.0
        self.temperature: float = 0.0
        self.terrain: str = "plains"
        self.zone: str = "temperate"
        self.hemisphere: str = "north"

        self.resource: Optional[Dict[str, Any]] = None
        self.resources: Resources = Resources()
        # This is the height of the tile in relation to the average sea level in meters.
        self.gameplay_height: int = 0

        # None is nature.
        self.player: Optional["Player"] = None

        # Base health and if damagable declarations.
        self.damagable: bool = False
        self.health: int = 100
        self.damage: int = 0

        # Does it take damage over time?
        self.damage_per_turn_mode: int = DamageMode.DAMAGE_NONE
        self.damage_per_turn: float = 0.0

        # Does it damage units over time?
        self.damage_per_turn_on_units_mode: int = DamageMode.DAMAGE_NONE
        self.damage_per_turn_on_units: float = 0.0

        # Does it damage improvements over time?
        self.damage_per_turn_on_improvements_mode: int = DamageMode.DAMAGE_NONE
        self.damage_per_turn_on_improvements: float = 0.0

        # Can units walk over?
        self.walkable: bool = True
        # Can ships make it through?
        self.sailable: bool = False
        # Is this deep water?
        self.deep: bool = False
        # Can airplanes fly over?
        self.flyable: bool = True
        # Is space above accessible?
        self.space_above: bool = True
        # Can it be dug under?
        self.diggable: bool = True
        # Can it be built on?
        self.buidable: bool = True
        # If it can be walked over with climbing.
        self.climbable: bool = True
        # If it can be claimed.
        self.claimable: bool = True
        # If units can breathe.
        self.air_breatheable: bool = True
        # Can things grow on it?
        self.growable: bool = True

        # How difficult it is to move over this tile measured in movement cost (MC).
        self.movement_cost: float = 1.0

        # What weather is the tile having?
        self.weather: Optional[BaseWeather] = None

        # What features does this tile contain?
        self.features: List[BaseFeature] = list()
        # Does this have any units?
        self.units: Units = Units()
        # Does this have improvements?
        self._improvements: ImprovementsSet = ImprovementsSet()
        # Does this have items sitting on top of it?
        self.items: List[BaseItem] = list()
        # What kind of states apply to this object?
        self.states: List[Any] = []

        # Does this contain a city?
        self.city: Optional["City"] = None
        # Who, if anybody, is the owner of this tile?
        self.owner: Optional["Player"] = None
        # Who has claimed the tile but does not own it?
        self.claimants: List[Any] = []
        # is this city being worked by a city?
        self.city_owner: Optional["City"] = None

        self.texture_card: Optional[NodePath | CardMaker] = None
        self.texture_card_texture: Optional[NodePath] = None

        self.city_name_group: Optional[NodePath] = None
        self.city_name_texture_card_texture: Optional[NodePath] = None

        self.inherit_passability_from_terrain: bool = True

        # We configure base tile yield mostly just for debugging.
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
        self.atlas: Optional[Any] = None
        self.atlas_width: Optional[int] = None
        self.atlas_height: Optional[int] = None

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

    @classmethod
    def generate_tag(cls, x: int, y: int) -> str:
        return f"tile_{x}_{y}"

    def on_load(self) -> None:
        self.tag = self.generate_tag(self.x, self.y)
        self.models = []
        self.base = Cache.get_showbase_instance()
        self._entity_manager = EntityManager.get_singleton_instance()
        self.logger = self.base.logger.gameplay.getChild("map.tile")

        self._render_default_terrain()
        self.create_root_ui_node()

        if self.tile_icon_group is None:
            raise AssertionError("Tile icon group not created.")

        self.text_card = NodePath("text_card")
        self.text_card.reparentTo(self.tile_icon_group)  # type: ignore

        self.rerender()

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

    def unregister(self):
        """Unregisters as a entity in the system."""
        from managers.entity import EntityType  # Prevent circular import

        self._entity_manager.unregister(entity=self, type=EntityType.TILE)

    def create_root_ui_node(self) -> None:
        self.texture_card = CardMaker(f"resource_icon_{self.id}")
        self.texture_card.setFrame(-0.05, 0.05, -0.05, 0.05)  # type: ignore

        self.city_name_group = NodePath("city_name_group")
        self.city_name_group.reparentTo(self.models[-1])  # type: ignore
        self.city_name_group.setCollideMask(BitMask32.bit(0))  # type: ignore

        self.tile_icon_group = NodePath("tile_icon_group")
        self.tile_icon_group.reparentTo(self.models[-1])  # type: ignore
        self.tile_icon_group.setCollideMask(BitMask32.bit(0))  # type: ignore

    def is_visisted_by(self, unit: "Unit") -> bool:
        messenger.send("unit.action.move.visiting_tile", [unit, self])
        self.logger.info(f"Unit {str(unit.tag)} is visiting tile {str(self.tag)}.")
        return True

    def add_city_name(self) -> None:
        if self.city is None:
            return

        if self.tile_icon_group is None:
            self.create_root_ui_node()

        if self.city_name_group is None:
            raise AssertionError("City name group not created.")

        from PIL import Image  # Needed for flip

        from helpers.images import generate_city_nameplate, pil_image_to_panda3d_texture
        from managers.assets import AssetManager

        # Load the assets
        left_img = AssetManager.load_pil_image("assets/icons/city_plate_left.png")
        middle_img = AssetManager.load_pil_image("assets/icons/city_plate_middle.png")
        right_img = AssetManager.load_pil_image("assets/icons/city_plate_right.png")
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
            star_img=AssetManager.load_pil_image("assets/icons/capital_icon.png"),
            star_offset_y=32,
            star_offset_x=-16,
            text_color=normalize_color_to_bytes(self.owner.color) if self.owner else (255, 0, 0, 255),  # type: ignore
        )

        # --- Stretch PIL canvas to force slim aspect ratio ---
        forced_aspect_ratio = 4.5
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

        city_np = self.city_name_group.attachNewNode(card_maker.generate())  # type: ignore
        city_np.setTexture(city_texture)
        city_np.setTransparency(True)
        city_np.setColor(1, 1, 1, 1)
        city_np.clearColorScale()
        # Proper orientation
        city_np.setHpr(0, 0, 0)
        city_np.setBillboardPointEye()
        city_np.setPos(0, 0, 2.8)
        city_np.setScale(1.0)

        city_np.setBin("fixed", 50)
        city_np.setDepthWrite(True)
        city_np.setDepthTest(True)
        city_np.setTwoSided(True)
        city_np.setAntialias(AntialiasAttrib.MAuto)

        if self.models:
            self.city_name_group.reparentTo(self.models[0])

    def add_icon_to_tile(self) -> None:
        """Apply shader overlay for resource icons using atlas UV rects."""
        if self.tile_icon_group is None:
            self.create_root_ui_node()

        if self.icon_overlay:
            self.icon_overlay.removeNode()
            self.icon_overlay = None
        if self.icon_overlay_card:
            self.icon_overlay_card = None
        if self.tile_icon_group:
            self.tile_icon_group.node().removeAllChildren()  # type: ignore

        resources = list(self.resources.flatten().values())
        basic_resource = self.get_tile_yield()

        if self.city:
            city_tile_yields = self.city.get_yield()
            basic_resource += city_tile_yields

        basic_resource = basic_resource.export_basic()

        self.icon_overlay_card = CardMaker(f"icon_overlay_{self.id}")
        self.icon_overlay_card.set_frame(-0.55, 0.55, -0.55, 0.85)  # type: ignore
        self.icon_overlay = NodePath(self.icon_overlay_card.generate())  # type: ignore
        self.icon_overlay.set_pos(0.1, 0, 0.17)  # type: ignore
        self.icon_overlay.set_hpr(90, -90, 0)  # type: ignore
        self.icon_overlay.set_scale(1.0)  # type: ignore
        self.icon_overlay.setTransparency(True)
        self.icon_overlay.setAttrib(ColorBlendAttrib.makeOff())  # type: ignore
        self.icon_overlay.setBin("fixed", 60)
        self.icon_overlay.reparent_to(self.tile_icon_group)  # type: ignore

        self.shader = Shader.load(  # type: ignore
            Shader.SL_GLSL, "assets/shaders/resource_icons.vert.glsl", "assets/shaders/resource_icons.frag.glsl"
        )
        self.icon_overlay.setShader(self.shader)  # type: ignore

        self.atlas = Cache.get_atlas()
        atlas_tex = self.atlas.get_panda3d_texture()
        atlas_tex.setWrapU(Texture.WMClamp)
        atlas_tex.setWrapV(Texture.WMClamp)
        atlas_tex.setFormat(Texture.F_srgb_alpha)
        atlas_tex.setMinfilter(SamplerState.FT_linear)
        atlas_tex.setMagfilter(SamplerState.FT_linear)
        atlas_tex.setAnisotropicDegree(0)
        self.icon_overlay.setShaderInput("icon_atlas", atlas_tex)
        self.atlas_width, self.atlas_height = self.atlas.atlas_image.size

        uv_rects = PTAFloat.emptyArray(4 * 7)  # 1 main + 6 small slots  # type: ignore

        # Fill slots
        slots: List[Optional[Union[str, BaseResource]]] = [None] * 7  # 0 = main, 1-6 = small
        if resources or self.city:
            if self.city:
                slots[0] = self.city.get_population_icon()
            else:
                slots[0] = resources[0]

        for i, resource in enumerate(basic_resource):
            slots[i + 1] = resource

        for i, res in enumerate(slots):
            if res is None:
                uv_rects[i * 4 + 0] = 0.0
                uv_rects[i * 4 + 1] = 0.0
                uv_rects[i * 4 + 2] = 0.0
                uv_rects[i * 4 + 3] = 0.0
                continue

            if isinstance(res, BaseResource) and res.value == 0:
                continue

            if i >= 1 and isinstance(res, BaseResource):
                virtual_path = res.get_numeric_icon()
            else:
                virtual_path = res if isinstance(res, str) else res.icon

            if self.atlas is None:
                raise AssertionError("Atlas not initialized.")

            pos = self.atlas.get_position_for_virtual_path(virtual_path)

            if pos is None:
                raise AssertionError(f"Position not found for virtual path: {virtual_path}")

            size = self.atlas.get_dimensions_for_virtual_path(virtual_path)
            if not size:
                continue

            x, y = pos
            w, h = size

            u0 = x / self.atlas_width
            v1 = 1.0 - (y / self.atlas_height)  # top
            u1 = (x + w) / self.atlas_width
            v0 = 1.0 - ((y + h) / self.atlas_height)  # bottom

            uv_rects[i * 4 + 0] = u0
            uv_rects[i * 4 + 1] = v0
            uv_rects[i * 4 + 2] = u1
            uv_rects[i * 4 + 3] = v1

        self.icon_overlay.setShaderInput("uv_rects", uv_rects)
        self.icon_overlay.setShaderInput("icon_count", 7)

        self._showing_large_icons = True

    def render(self, render_all: bool = True, model_index: Optional[int] = None) -> None:
        if not self.tile_terrain:
            self.logger.warning(f"Tile {self} has no terrain set, not rendering.")
            return

        self.set_color(Colors.RESTORE)
        self.calculate()

        if not self.models and len(self.improvements()) == 0:
            self._render_default_terrain()
            self.create_root_ui_node()
            self._render_resource_model()
            return

        if render_all:
            self.unrender_all()
            self._render_improvements()
            self._render_default_terrain()
            self._render_resource_model()
            self.create_root_ui_node()
        elif model_index is not None:
            self.unrender_model(model_index)
            if model_index == 0:
                self._render_default_terrain()
            elif model_index == 1:
                self._render_improvements()
            self.create_root_ui_node()
        else:
            self._render_default_terrain()
            self.create_root_ui_node()

        # Clear old icon overlay
        if self.icon_overlay is not None:
            self.icon_overlay.removeNode()
            self.icon_overlay = None

        self.add_icon_to_tile()

        if self.city is not None:
            self.add_city_name()

    def _render_resource_model(self) -> None:
        if self.city is not None:
            return
        resource = list(self.resources.flatten_non_mechanic().values())

        if len(resource) == 0:
            return

        resource = resource[0]

        if resource.model is None:
            return

        self.add_model(resource.model, resource.model_position, resource.model_size, resource.model_hpr)

    def on_turn_end(self, turn: int) -> None:
        """Will only be called by the world manager. when the tile has an effect, unit, city or player."""
        if len(self._improvements) > 0:  # We only process improvements if we have any.
            self._improvements.on_turn_end(turn)

        if len(self.effects) > 0:
            self.effects.on_turn_end(turn)

        if self.city:
            self.add_icon_to_tile()

    def _render_default_terrain(self) -> None:
        # Get the model path from the terrain (kept as a relative path)
        model_path: str = str(self.tile_terrain.model())
        # Resolve the full path to the model file
        full_model_path: str = realpath(join(dirname(__file__), "../..", model_path))

        # Load the model using the full path
        hex_model: NodePath | None = self.base.loader.loadModel(full_model_path)

        if hex_model is None:
            raise AssertionError(f"Model not found: {full_model_path}")

        hex_model.setScale(0.48)
        hex_model.setHpr(270, 0, 0)

        node: NodePath = hex_model.copyTo(self.base.render)  # type: ignore
        node.setPos(self.pos_x, self.pos_y, 0)
        node.setCollideMask(BitMask32.bit(1))  # type: ignore
        self.tag = self.generate_tag(self.x, self.y)
        node.setTag("tile_id", self.tag)
        self.models.append(node)

    def _render_improvements(self) -> None:
        improvements: List[Improvement] = self.improvements().get_all()
        for improvement in improvements:
            model_path = improvement.get_model_path()

            if model_path is None:
                continue

            self.add_model(
                model_path=model_path,
                pos_offset=improvement._model_offset,  # type: ignore
                scale=improvement._model_scale,  # type: ignore
                hpr=improvement._model_hpr,  # type: ignore
            )

    def add_model(
        self,
        model_path: str,
        pos_offset: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        scale: float = 1.0,
        hpr: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> None:
        """
        Add an additional model on top of the tile.
        """
        base_path: Path = self.base.get_base_path()
        extra_model: NodePath | None = self.base.loader.loadModel(abspath(join(base_path, model_path)))

        if extra_model is None:
            raise AssertionError(f"Model not found: {model_path}")

        extra_model.setScale(0.48 * scale)
        extra_model.setHpr(*hpr)
        node: NodePath = extra_model.copyTo(self.base.render)  # type: ignore
        node.setPos(self.pos_x + pos_offset[0], self.pos_y + pos_offset[1], pos_offset[2])
        node.setCollideMask(BitMask32.bit(1))  # type: ignore
        self.models.append(node)

        if self.tag is None:
            raise AssertionError("Tile tag is not set.")

        node.setTag("tile_id", self.tag)
        if self.models:
            self.models[0] = node
        else:
            self.models.append(node)

    def unrender(self) -> None:
        """
        Remove the tile from the scene by unrendering all models.
        """
        self.unrender_all()

    def unrender_all(self, icons: bool = False) -> None:
        for node in self.models:
            node.removeNode()
        self.models.clear()

    def unrender_model(self, model_index: int) -> None:
        """
        Remove a specific model by its index in the models list.
        """
        if 0 <= model_index < len(self.models):
            self.models[model_index].removeNode()
            del self.models[model_index]

    def rerender(self) -> None:
        """
        Refresh the tile's visual representation by unrendering and then rendering.
        """
        self.render()

    def set_color(self, color: Tuple[float, float, float, float]) -> None:
        """
        Set the color of all rendered models on this tile.
        """
        for node in self.models:
            node.setColor(*color)

    def get_node(self) -> Optional[NodePath]:
        """
        Return the first rendered model (typically the terrain) or None if no model exists.
        """
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
        return str(self.tile_terrain.model()) if self.tile_terrain else ""

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
        unit.tile = self
        self.units.add_unit(unit)

    def remove_unit(self, unit: "Unit") -> None:
        del unit.tile
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
            "x": self.x,
            "y": self.y,
            "terrain": terrain_name,
            "model": self.model(),
            "passable": f"{str(self.passable)}, {str(self.passable_without_tech)}",
            "movement_cost": self.movement_cost,
            "texture": self.texture(),
            "class": self.__class__.__name__,
            "owner": str(self.owner.name) if self.owner else t_("civilization.nature.name"),
            "city": self.city,
            "improvements": " | ".join(_improvements),
            "tile_yield": str(yields),
            "temperature": self.temperature,
            "resources": self.resources.flatten(),
            "features": self.features,
            "units": ",".join(_units),
            "health": self.health,
            "damage": self.damage,
            "pos": (self.pos_x, self.pos_y, self.pos_z),
            "Hpr": (),
            "effects": ",".join(self.effects.get_effects().keys()),
            "resource_improved": "Yes" if self.is_resource_improved() else "No",
        }

        data["hex_data"] = {
            "altitude": self.altitude,
            "biome": f"{self.biome.id} - {self.biome.name}",  # type: ignore
            "moisture": self.moisture,
            "is_coast": self.is_coast,
            "is_water": self.is_water,
            "is_land": self.is_land,
            "is_lake": self.is_lake,
            "is_city": self.is_city(),
            "terrain": self.terrain,
            "zone": self.zone,
            "hemisphere": self.hemisphere,
            "resource['rating']": self.resource["rating"] if self.resource else None,
            "resource['type']": self.resource["type"] if self.resource else None,
        }

        data["hex_data"] = "\n".join(f"{k}: {v}" for k, v in data["hex_data"].items())

        if self.city is not None:
            data["city"] = {
                "city_name": self.city.name,
                "owned_tiles": ",".join(str(tile.tag) for tile in self.city.owned_tiles if tile.tag is not None),
                "population": self.city.population,
                "is_capital": self.city.is_capital,
                "is_building": self.city.is_building,
                "building": self.city.building,
                "resources_needed": f"{self.city.resource_required_amount}/{self.city.resource_collected}",
            }
            data["city"] = "\n".join(f"{k}: {v}" for k, v in data["city"].items())

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

        self.set_terrain(CityTerrain())

        self.owner = player
        self.owner.tiles.add_tile(self)

        if self.owner.capital is not None:
            self.owner.capital.de_capitalize()

        self.owner.capital = self.city

        self.calculate()
        self.rerender()
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
        self.rerender()
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

    def enrich_from_extra_data(self, hex: Hex) -> None:
        self.altitude = hex.altitude
        self.biome = hex.biome  # type: ignore
        self.moisture = hex.moisture
        self.temperature = hex.base_temperature[0]
        self.terrain = hex.terrain  # type: ignore
        self.zone = hex.zone.name  # type: ignore
        self.hemisphere = hex.hemisphere.name
        self.is_coast = hex.is_coast
        self.is_water = hex.is_water
        self.is_land = hex.is_land
        self.is_sea = hex.geoform_type.id == 2  # type: ignore # 2 == Sea
        self.is_lake = hex.geoform_type.id == 4  # type: ignore # 4 == Lake
        resource: Type[BaseResource] | None = hex.get_gameplay_resource()
        if resource is not None:
            self.instance_resource(resource)

    def is_showing_large_icons(self) -> bool:
        return self._showing_large_icons

    def destroy(self):
        self._entity_manager.unregister(entity=self, type=EntityType.TILE)
        self.unrender_all()
        self.destroyed = True
