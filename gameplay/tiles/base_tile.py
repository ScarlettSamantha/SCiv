from copy import deepcopy
from enum import Enum
from logging import Logger
from os.path import dirname, join, realpath
from pathlib import Path
from posixpath import abspath
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Tuple, Type, Union

from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase.MessengerGlobal import messenger
from panda3d.core import AntialiasAttrib, BitMask32, CardMaker, LRGBColor, NodePath, TextNode, Texture

from gameplay._units import Units
from gameplay.combat.damage import DamageMode
from gameplay.condition import Conditions
from gameplay.improvement import Improvement
from gameplay.improvements_set import ImprovementsSet
from gameplay.resource import BaseResource, Resources
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.weather import BaseWeather
from gameplay.yields import Yields
from helpers.colors import Colors, Tuple4f
from managers.assets import AssetManager
from managers.entity import EntityManager, EntityType
from managers.i18n import T_TranslationOrStr, _t
from managers.player import Player, PlayerManager
from system.effects import Effects
from system.entity import BaseEntity
from system.subsystems.hexgen.hex import Hex
from world.features._base_feature import BaseFeature
from world.items._base_item import BaseItem

if TYPE_CHECKING:
    from gameplay.city import City
    from gameplay.units.unit_base import UnitBaseClass


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
        extra_data: Optional[dict] = None,
    ) -> None:
        self.id: int = id(self)
        self.x: int = x
        self.y: int = y
        super().__init__()
        self.pos_x: float = pos_x
        self.pos_y: float = pos_y
        self.pos_z: float = pos_z
        self.hpr: Tuple[float, float, float] = (0.0, 0.0, 0.0)

        self._entity_manager = EntityManager.get_instance()
        self.logger: Logger = self.base.logger.gameplay.getChild("map.tile")

        self.extra_data: Optional[dict] = extra_data

        self.destroyed: bool = False
        self.grid_position: Optional[Any] = None
        self.raw_position: Optional[Any] = None
        self.tag: Optional[str] = None
        # Instead of a single node, we keep a list of NodePaths.

        self.models: List[NodePath] = []
        self.extra_data: Optional[dict] = extra_data

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

        self.resource: Optional[dict] = None
        self.resources: Resources = Resources()
        # This is the height of the tile in relation to the average sea level in meters.
        self.gameplay_height: int = 0

        # None is nature.
        self.player: Optional[Player] = None

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
        self.owner: Optional[Player] = None
        # Who has claimed the tile but does not own it?
        self.claimants: List[Any] = []
        # is this city being worked by a city?
        self.city_owner: Optional["City"] = None

        self.texture_card: Optional[NodePath] = None
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

        self._showing_small_icons: bool = False
        self._showing_large_icons: bool = False

        self.effects: Effects = Effects(self)
        self.needs_tile_proecessing: bool = False

        self.tile_icon_group: Optional[NodePath] = None
        self.mini_icons_card: Optional[NodePath] = None
        self.text_card: Optional[NodePath] = None

    @property
    def tile_terrain(self) -> BaseTerrain:
        return self._tile_terrain

    @tile_terrain.setter
    def tile_terrain(self, value: BaseTerrain) -> None:
        self._tile_terrain = value
        if self.inherit_passability_from_terrain:
            self.passable: bool = True if self.tile_terrain is None or self.tile_terrain.passable is True else False
            self.passable_without_tech: bool = (
                True if self.tile_terrain is None or self.tile_terrain.passable_without_tech is True else False
            )

    @classmethod
    def generate_tag(cls, x: int, y: int) -> str:
        return f"tile_{x}_{y}"

    def calculate(self):
        base = deepcopy(self._tile_terrain.get_tile_yield())  # This is to prevent modifying the base yield.

        for improvement in self._improvements.get_all():
            base += improvement.tile_yield

        for effect in self.effects.get_effects().values():
            base += effect.yield_impact

        self.tile_yield = base

    def get_pos(self) -> Tuple[float, float, float]:
        return self.pos_x, self.pos_y, self.pos_z

    def __repr__(self) -> str:
        return f"{self.id}@{self.x},{self.y}"

    def register(self):
        """Registers as a entity in the system."""
        from managers.entity import EntityType  # Prevent circular import

        self._entity_manager.register(entity=self, key=str(self.id), type=EntityType.TILE)

    def unregister(self):
        """Unregisters as a entity in the system."""
        from managers.entity import EntityType  # Prevent circular import

        self._entity_manager.unregister(entity=self, type=EntityType.TILE)

    def clear_large_icons(self) -> None:
        """
        Remove the main texture icon from the tile.
        """
        if self.tile_icon_group is not None:
            self.tile_icon_group.removeNode()
            self.tile_icon_group = None
            self._showing_large_icons = False

    def clear_small_icons(self) -> None:
        """
        Remove all small icons and text overlays from the tile.
        """
        if self.mini_icons_card is not None:
            self.mini_icons_card.removeNode()
            self.mini_icons_card = None
            self._showing_small_icons = False
        if self.text_card is not None:
            self.text_card.removeNode()
            self.text_card = None

    def clear_all_icons(self) -> None:
        """
        Remove all icons from the tile.
        """
        self.clear_large_icons()
        self.clear_small_icons()

    def create_root_ui_node(self) -> None:
        self.texture_card = CardMaker(f"resource_icon_{self.id}")
        self.texture_card.setFrame(-0.05, 0.05, -0.05, 0.05)

        self.city_name_group = NodePath("city_name_group")
        self.city_name_group.reparentTo(self.models[0])
        self.city_name_group.setCollideMask(BitMask32.bit(0))

        self.tile_icon_group = NodePath("tile_icon_group")
        self.tile_icon_group.reparentTo(self.models[0])
        self.tile_icon_group.setCollideMask(BitMask32.bit(0))

    def is_visisted_by(self, unit: "UnitBaseClass") -> bool:
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

        city_text = TextNode("city_name_text")
        city_text.setText(self.city.name)

        # Load the font
        font = AssetManager.load_font("assets/fonts/Washington.ttf")
        if font:
            font.setPolyMargin(0.01)  # Improve clarity
            try:
                font.setPixelsPerUnit(250)  # Improve clarity
            except AssertionError:
                pass  # For some reason some letters are not showing up. This is a workaround. they are replaced with []
            city_text.setFont(font)

        # Load and verify texture
        texture = AssetManager.load_texture("assets/city_name_border.png")
        if not texture:
            raise RuntimeError("Failed to load city name border texture.")
        city_text.setCardTexture(texture)

        # Set text appearance
        text_color: Tuple4f = Colors.WHITE if self.city.player is None else self.city.player.color
        city_text.setTextColor(*text_color)
        city_text.setAlign(TextNode.ACenter)
        city_text.setCardDecal(True)

        if self.city.is_capital:
            city_text.setCardAsMargin(0.5, 0.2, 0.25, 0.25)
        else:
            city_text.setCardAsMargin(0.3, 0.3, 0.25, 0.25)

        city_np = self.city_name_group.attachNewNode(city_text)

        city_np.setPos(0, 0, 2.8)  # Position it above the city
        city_np.setHpr((0, 45, 0))

        # Ensure a fixed card size
        card_size = 1.0  # Keep the card size fixed
        city_np.setScale(card_size)

        # Handle text overflow by adjusting text scale
        max_width = 2.0  # Max width the text should fit within
        base_font_size = 1.0  # Default font scale

        text_width = city_text.getWidth()
        if text_width > max_width:
            text_scale = max_width / text_width
        else:
            text_scale = base_font_size

        city_text.set_glyph_scale(text_scale)  # type: ignore

        # Ensure visibility and proper rendering
        city_np.setTransparency(True)
        city_np.setCollideMask(BitMask32.bit(0))
        city_np.setBin("fixed", 50)
        city_np.setDepthWrite(True)
        city_np.setDepthTest(True)
        city_np.setTwoSided(True)
        city_np.setAntialias(AntialiasAttrib.MAuto)
        city_np.set_billboard_point_eye()  # Always face the camera.

        # If the city is the capital, add an icon before the name
        if self.city.is_capital:
            capital_icon = OnscreenImage(image="assets/icons/capital_icon.png")
            capital_icon.reparentTo(city_np)
            capital_icon.setScale(0.2)  # Adjust size as needed
            capital_icon.set_antialias(AntialiasAttrib.MAuto)  # type: ignore
            capital_icon.setTransparency(True)

            capital_icon.setBin("fixed", 51)  # Higher than text
            capital_icon.setDepthWrite(False)
            capital_icon.setDepthTest(False)
            capital_icon.setPos(-1.25, 0.265, 0)

        # Ensure the city_name_group is reparented to a visible node.
        if self.models:
            self.city_name_group.reparentTo(self.models[0])

    def add_icon_to_tile(self) -> None:
        """
        Append the texture as a separate node instead of replacing existing models,
        then set up the structure to later add mini icons and text overlays as separate cards.
        """
        resources: Dict[str, BaseResource] = self.resources.flatten()
        resource = list(resources.values())[0] if resources else None

        if self.tile_icon_group is None:
            self.create_root_ui_node()

        if resource is not None:
            texture_path = resource.icon
            if not texture_path:
                raise AssertionError(f"Resource {resource} has no icon set, cannot add texture.")

            # Create the main texture card node
            self.texture_card_texture = NodePath(self.texture_card.generate())  # type: ignore
            if texture_path not in self.texture_cache:
                self.texture_cache[texture_path] = self.base.loader.load_texture(texturePath=texture_path)
                self.texture_cache[texture_path].set_format(Texture.F_srgb_alpha)  # type: ignore
            texture = self.texture_cache[texture_path]

            if not self.models:
                return

            # Reparent the main icon card to the common group.
            self.texture_card_texture.reparentTo(self.tile_icon_group)
            self.texture_card_texture.setTexture(texture, 1)
            self.texture_card_texture.setPos((-0.55, 0, 0.151))
            self.texture_card_texture.setHpr((0, 270, 270))
            self.texture_card_texture.setScale(6.0)
            self.texture_card_texture.setTransparency(True)

            self._showing_large_icons = True

    def add_small_icons(self, force: bool = False) -> None:
        city_tile_yields: Yields = Yields.nullYield()
        if self.city is not None:
            for improvement in self.city._improvements.get_all():
                city_tile_yields += improvement.tile_yield_improvement

        yields = self.tile_yield + city_tile_yields
        basic_resources: List[BaseResource] = yields.export_basic()

        if len(basic_resources) == 0:
            return

        if self.tile_icon_group is None:
            self.create_root_ui_node()

        # Create a separate node for mini icons if not already created.
        if self.mini_icons_card is None or force:
            self.mini_icons_card = NodePath("mini_icons_card")
            self.mini_icons_card.reparentTo(self.tile_icon_group)

        # Create a separate node for text overlays if not already created.
        if self.text_card is None or force:
            self.text_card = NodePath("text_card")
            self.text_card.reparentTo(self.tile_icon_group)

        # Define grid positions relative to the tile icon group.
        grid_positions: List[Tuple[float, float, float]] = [
            # top-bottom (- is up), left-right (- is left), z
            (0.2, -0.48, 0.18),  # Top row, left # gold
            (0.33, 0.0, 0.18),  # Top row, center # production
            (0.15, 0.52, 0.18),  # Top row, right # food
            (0.65, -0.35, 0.18),  # Bottom row, left # science
            (0.65, 0.3, 0.18),  # Bottom row, right # culture
        ]
        grid_positions_text: List[Tuple[float, float, float]] = [
            (0.25, -0.5, -0.20),  # Top row, left
            (0.40, 0, -0.20),  # Top row, center
            (0.25, 0.5, -0.2),  # Top row, right
            (0.8, -0.4, -0.2),  # Bottom row, left
            (0.8, 0.4, -0.2),  # Bottom row, right
        ]
        font = AssetManager.load_font("assets/fonts/Washington.ttf")

        for i, resource in enumerate(basic_resources):
            icon_path = resource.icon

            # Create mini icon card.
            small_icon_card = CardMaker("small_icon")
            small_icon_card.setFrame(-0.05, 0.05, -0.05, 0.05)
            small_icon_np = NodePath(small_icon_card.generate())  # type: ignore

            if icon_path not in self.texture_cache:
                self.texture_cache[icon_path] = AssetManager.load_texture(path=icon_path)
                self.texture_cache[icon_path].set_format(Texture.F_srgb_alpha)  # type: ignore
            texture = self.texture_cache[icon_path]

            if not texture:
                raise AssertionError(f"Failed to load texture for small icon: {icon_path}")

            small_icon_np.setTexture(texture, 1)
            small_icon_np.setPos(grid_positions[i])
            small_icon_np.setHpr(0, 270, -90)
            small_icon_np.setScale(3.0)
            small_icon_np.setTransparency(True)
            small_icon_np.setCollideMask(BitMask32.bit(0))
            # Attach mini icon to its dedicated card.
            small_icon_np.reparentTo(self.mini_icons_card)

            # Create a text node for the number overlay.
            text_node = TextNode(f"icon_counter_{i}")
            text_node.setText(str(int(resource.value)))
            text_node.setFont(font)
            text_node.setTextColor(1, 1, 1, 1)  # White text.
            text_node.setAlign(TextNode.ACenter)
            text_node.setShadow(0, 0)  # Slight shadow.
            text_node.setShadowColor(0, 0, 0, 1)  # Black shadow.

            # Attach the text node to the separate text card.
            text_np = self.text_card.attachNewNode(text_node)
            # Position the text above the mini icon.
            x, y, z = grid_positions_text[i]
            text_np.setHpr(90, -90, 0)
            text_np.setPos(x, y, z + 0.4)
            text_np.setScale(0.3)
        self._showing_small_icons = True

    def render(self, render_all: bool = True, model_index: Optional[int] = None) -> None:
        """
        Render the tile.
        - If no models have been rendered yet, the default terrain model is loaded.
        - If render_all is True, all models are unrendered and the default terrain is re-rendered.
        - If model_index is provided, only that model is unrendered and re-rendered.
        """
        if not self.tile_terrain:
            print(f"Tile {self} has no terrain set, not rendering.")
            return
        self.set_color(Colors.RESTORE)
        self.calculate()

        # If no models exist, render the default terrain.
        if not self.models and len(self.improvements()) == 0:
            self._render_default_terrain()
            return

        if render_all:
            self._render_improvements()
            self._render_default_terrain()

            # (Additional models could be re-added here if needed.)
        elif model_index is not None:
            self.unrender_model(model_index)
            if model_index == 0:
                self._render_default_terrain()
            elif model_index == 1:
                self._render_improvements()
            # Custom logic for re-rendering other models can be added here.
        else:
            self._render_default_terrain()

        if self._showing_large_icons:
            self.clear_large_icons()
            self.add_icon_to_tile()
        if self._showing_small_icons:
            self.clear_small_icons()
            self.add_small_icons()
        if self.city is not None:
            self.add_city_name()

    def on_turn_end(self, turn: int) -> None:
        """Will only be called by the world manager. when the tile has an effect, unit, city or player."""
        if len(self._improvements) > 0:  # We only process improvements if we have any.
            self._improvements.on_turn_end(turn)

        if len(self.effects) > 0:
            self.effects.on_turn_end(turn)

    def _render_default_terrain(self) -> None:
        if self.tile_terrain is None:
            print(f"Tile {self} has no terrain set, cannot render default terrain.")
            return

        # Get the model path from the terrain (kept as a relative path)
        model_path: str = str(self.tile_terrain.model())
        # Resolve the full path to the model file
        full_model_path: str = realpath(join(dirname(__file__), "../..", model_path))

        # Load the model using the full path
        hex_model: NodePath = self.base.loader.loadModel(full_model_path)
        if hex_model is None:
            raise AssertionError(f"Model not found: {full_model_path}")

        hex_model.setScale(0.48)
        hex_model.setHpr(270, 0, 0)

        node: NodePath = hex_model.copyTo(self.base.render)
        node.setPos(self.pos_x, self.pos_y, 0)
        node.setCollideMask(BitMask32.bit(1))
        self.tag = self.generate_tag(self.x, self.y)
        node.setTag("tile_id", self.tag)
        if self.models:
            self.models[0] = node
        else:
            self.models.append(node)

    def _render_improvements(self) -> None:
        improvements: List[Improvement] = self.improvements().get_all()
        for improvement in improvements:
            model_path = improvement.get_model_path()

            if model_path is None:
                continue

            self.add_model(
                model_path=model_path,
                pos_offset=improvement._model_offset,
                scale=improvement._model_scale,
                hpr=improvement._model_hpr,
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
        extra_model: NodePath = self.base.loader.loadModel(abspath(join(base_path, model_path)))

        if extra_model is None:
            raise AssertionError(f"Model not found: {model_path}")

        extra_model.setScale(0.48 * scale)
        extra_model.setHpr(*hpr)
        node: NodePath = extra_model.copyTo(self.base.render)
        node.setPos(self.pos_x + pos_offset[0], self.pos_y + pos_offset[1], pos_offset[2])
        node.setCollideMask(BitMask32.bit(1))
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
        """
        Remove all models from the scene.
        """
        if icons:
            self.clear_all_icons()
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
        else:
            print(f"No model at index {model_index} to unrender.")

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

    def set_terrain(self, terrain: BaseTerrain) -> None:
        self.tile_terrain = terrain

    def get_terrain(self) -> BaseTerrain:
        if self.tile_terrain is None:
            raise AssertionError("Tile terrain is not set.")
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
            print(f"No terrain set for tile, returning default color: {self.__class__.__name__}")
            return (0, 0, 0)

    def model(self) -> str:
        return str(self.tile_terrain.model()) if self.tile_terrain else ""

    def texture(self) -> T_TranslationOrStr:
        return self.tile_terrain.texture() if self.tile_terrain else ""

    def addTileYield(self, tileYield: Yields) -> None:
        self.tile_yield.values += tileYield  # type: ignore

    def get_tile_yield(self) -> Yields:
        return self.tile_yield

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

    def add_unit(self, unit: "UnitBaseClass") -> None:
        unit.tile = self
        self.units.add_unit(unit)

    def remove_unit(self, unit: "UnitBaseClass") -> None:
        del unit.tile
        # Assuming the intent is to remove the unit.
        self.units.remove_unit(unit)

    def is_occupied(self) -> bool:
        return len(self.units._units) > 0 or self.city is not None

    def to_gui(self) -> Dict[str, Any]:
        terrain = self.get_terrain()
        if terrain is not None:
            terrain_name: T_TranslationOrStr = terrain.name
        else:
            terrain_name: T_TranslationOrStr = "civilization.nature.name"

        _improvements = []
        if self.city is not None:  # We add the city improvements to the list of improvements.
            _improvements += [str(improvement.name) for improvement in self.city.get_improvements()]
        for improvement in self._improvements.get_all():
            _improvements.append(str(improvement.name))

        _units = []
        for unit in self.units._units:
            data = unit.to_gui()
            _units.append(f"{data['tag']} {data['name']}")

        data = {
            "tag": self.tag,
            "x": self.x,
            "y": self.y,
            "terrain": terrain_name,
            "model": self.model(),
            "passable": f"{str(self.passable)}, {str(self.passable_without_tech)}",
            "movement_cost": self.movement_cost,
            "texture": self.texture(),
            "class": self.__class__.__name__,
            "owner": str(self.owner.name) if self.owner else _t("civilization.nature.name"),
            "city": self.city,
            "improvements": " | ".join(_improvements),
            "tile_yield": str(self.tile_yield),
            "resources": self.resources.flatten(),
            "features": self.features,
            "units": ",".join(_units),
            "health": self.health,
            "damage": self.damage,
            "pos": (self.pos_x, self.pos_y, self.pos_z),
            "Hpr": (),
            "effects": ",".join(self.effects.get_effects().keys()),
        }

        if isinstance(self.extra_data, Hex):
            data["hex_data"] = {
                "altitude": self.altitude,
                "biome": f"{self.biome.id} - {self.biome.name}",  # type: ignore
                "moisture": self.moisture,
                "temperature": f"{self.extra_data.base_temperature[0]}, {self.extra_data.base_temperature[1]}",
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
        player: Optional[Player] = None,
        population: int = 1,
        capital: Optional[bool] = None,  # None is Auto detect
    ) -> bool:
        """
        Found a city on this tile. If no player is provided, the current player is used.
        If no population is provided, the default is 1. If no capital is provided, the default is True if the player has no cities.

        The messeging system is used to inform the player of the city being founded via the action(gameplay.actions.unit.found) that calls this mostly.
        """
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

        self.unrender_model(0)
        self.set_terrain(CityTerrain())
        self.owner = player
        self.owner.tiles.add_tile(self)
        if self.owner.capital is not None:  # we have a capital
            self.owner.capital.de_capitalize()  # We tell the current capital to de-capitalize so it can be done with something in the future, for now its just a property set.
        self.owner.capital = self.city

        self._render_default_terrain()
        self.add_city_name()
        return True

    def build(self, improvement: Improvement) -> Literal[True] | CantBuildReason:
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

    def destroy_improvement(self, improvement: Improvement) -> None:
        self._improvements.remove(improvement)
        improvement.on_destroy()

    def get_buildable_improvements(self) -> List[Type[Improvement]]:
        return self.get_terrain().supported_improvements()

    def get_cords(self) -> Tuple[float, float, float]:
        return self.pos_x, self.pos_y, self.pos_z

    def get_map_cords(self) -> Tuple[int, int]:
        return self.x, self.y

    def instance_resource(self, resource: Type[BaseResource]):
        """Just here to decouplel it from enrich from extra data as it will be gone soon."""
        self.resources.add(resource(3), auto_instance=True)

    def enrich_from_extra_data(self, hex: Hex) -> None:
        self.extra_data = hex  # type: ignore
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

    def destroy(self):
        self._entity_manager.unregister(entity=self, type=EntityType.TILE)
        self.unrender_all()
        self.destroyed = True
