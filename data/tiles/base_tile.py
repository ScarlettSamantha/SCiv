from panda3d.core import NodePath, LRGBColor, BitMask32
from typing import Any, Optional, List, Tuple, Union
from os.path import dirname, realpath, join
from data.terrain._base_terrain import BaseTerrain
from gameplay._units import Units
from gameplay.combat.damage import DamageMode
from gameplay.improvement import Improvement
from gameplay.units.unit_base import UnitBaseClass
from gameplay.weather import BaseWeather
from gameplay.improvements import Improvements
from gameplay.tile_yield_modifier import TileYieldModifier, TileYield
from gameplay.city import City
from hexgen.hex import Hex
from world.features._base_feature import BaseFeature
from world.items._base_item import BaseItem
from managers.player import PlayerManager, Player
from managers.i18n import T_TranslationOrStr, _t, get_i18n
from system.entity import BaseEntity
from managers.entity import EntityManager, EntityType


class BaseTile(BaseEntity):
    def __init__(
        self,
        base: Any,
        x: int = 0,
        y: int = 0,
        pos_x: float = 0.0,
        pos_y: float = 0.0,
        pos_z: float = 0.0,
        extra_data: Optional[dict] = None,
    ) -> None:
        self.id: int = id(self)
        self.x: int = x
        self.base: Any = base
        self.y: int = y
        self.pos_x: float = pos_x
        self.pos_y: float = pos_y
        self.pos_z: float = pos_z
        self.hpr: Tuple[float, float, float] = (0.0, 0.0, 0.0)

        self._entity_manager = EntityManager.get_instance()

        self.extra_data: Optional[dict] = extra_data

        self.tile_terrain: Optional[BaseTerrain] = None
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
        self._improvements: Improvements = Improvements()
        # Does this have items sitting on top of it?
        self.items: List[BaseItem] = list()
        # What kind of states apply to this object?
        self.states: List[Any] = []

        # Does this contain a city?
        self.city: Optional[City] = None
        # Who, if anybody, is the owner of this tile?
        self.owner: Optional[Player] = None
        # Who has claimed the tile but does not own it?
        self.claimants: List[Any] = []

        # We configure base tile yield mostly just for debugging.
        self.tile_yield: TileYieldModifier = TileYieldModifier(
            values=TileYield(
                gold=0.0,
                production=0.0,
                science=0.0,
                food=0.0,
                culture=0.0,
                housing=0.0,
            ),
            mode=TileYieldModifier.MODE_SET,
        )

        self.meshCollider: bool = True

    @classmethod
    def generate_tag(cls, x: int, y: int) -> str:
        return f"tile_{x}_{y}"

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

        # If no models exist, render the default terrain.
        if not self.models:
            self._render_default_terrain()
            return

        if render_all:
            self.unrender_all()
            self._render_default_terrain()
            # (Additional models could be re-added here if needed.)
        elif model_index is not None:
            self.unrender_model(model_index)
            if model_index == 0:
                self._render_default_terrain()
            # Custom logic for re-rendering other models can be added here.
        else:
            self._render_default_terrain()

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

        # For each texture in the model, reload it using its full path
        # but then set the texture's filename back to the original relative path.
        # texture = hex_model.findAllTextures()[0]
        # Get the original relative filename from the texture
        # original_rel_filename = texture.getFilename().getFullpath()
        # Resolve the texture's full path relative to the model file's directory
        # full_texture_path = realpath(
        #    join(dirname(full_model_path), original_rel_filename)
        # )

        # if not os.path.exists(full_model_path):
        #    raise OSError(f"Texture file not found: {full_texture_path}")

        # Load the texture using its full path
        # new_texture = self.base.loader.loadTexture(full_model_path)
        # Restore the original filename (relative) on the texture object
        # new_texture.setFilename(original_rel_filename)
        # Replace the old texture with the newly loaded one
        # hex_model.setTexture(new_texture, 1)

        # Apply consistent styling.
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
        extra_model: NodePath = self.base.loader.loadModel(model_path)
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

    def unrender_all(self) -> None:
        """
        Remove all models from the scene.
        """
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
        self.unrender_all()
        self._render_default_terrain()
        # (Additional models can be re-added using add_model() if required.)

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

    def get_terrain(self) -> Optional[BaseTerrain]:
        return self.tile_terrain

    def get_climbable(self) -> bool:
        return self.climbable

    def is_spawnable_upon(self, on_other_units: bool = False, on_mountains: bool = False) -> bool:
        return (
            not self.is_water
            and not self.is_sea
            and (on_other_units or len(self.units) == 0)
            and not self.city
            and (on_mountains or self.altitude < 200)  # No spawning on mountains
        )

    def is_passable(self) -> bool:
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

    def setTerrain(self, terrain: BaseTerrain) -> None:
        self.tile_terrain = terrain

    def addTileYield(self, tileYield: TileYield) -> None:
        self.tile_yield.values += tileYield  # type: ignore

    def tileYield(self) -> TileYieldModifier:
        return self.tile_yield

    def improvements(self) -> Improvements:
        return self._improvements

    def is_city(self) -> bool:
        return self.city is not None

    def build(self, improvement: Improvement) -> None:
        self._improvements.add(improvement)

    def add_unit(self, unit: UnitBaseClass) -> None:
        unit.tile = self
        if unit.base is None:
            unit.base = self.base
        self.units.add_unit(unit)

    def remove_unit(self, unit: UnitBaseClass) -> None:
        del unit.tile
        # Assuming the intent is to remove the unit.
        self.units.remove_unit(unit)

    def is_occupied(self) -> bool:
        return len(self.units.units) > 0 or self.city is not None

    def to_gui(self) -> dict[str, Any]:
        terrain = self.get_terrain()
        if terrain is not None:
            terrain_name: T_TranslationOrStr = terrain.name
        else:
            terrain_name: T_TranslationOrStr = "civilization.nature.name"

        _improvements = []
        for improvement in self._improvements.get_all():
            _improvements.append(get_i18n().lookup(improvement.name))

        _units = []
        for unit in self.units.units:
            data = unit.to_gui()
            _units.append(f"{data['tag']} {data['name']}")

        data = {
            "tag": self.tag,
            "x": self.x,
            "y": self.y,
            "terrain": terrain_name,
            "model": self.model,
            "texture": self.texture(),
            "class": self.__class__.__name__,
            "owner": self.owner if self.owner else _t("civilization.nature.name"),
            "city": self.city,
            "improvements": " | ".join(_improvements),
            "features": self.features,
            "units": ",".join(_units),
            "health": self.health,
            "damage": self.damage,
            "pos": (self.pos_x, self.pos_y, self.pos_z),
            "Hpr": (),
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

        return data

    def found(
        self,
        player: Optional[Player] = None,
        population: int = 1,
        capital: bool = False,
    ) -> None:
        from data.terrain.city import City as CityTerrain

        if player is None:
            player = PlayerManager.player()

        self.city = City.found_new(name="Test city", owner=player, tile=self, population=population, is_capital=capital)
        self.unrender_model(0)
        self.setTerrain(CityTerrain())
        self.owner = player
        self.owner.tiles.add_tile(self)
        self.owner.cities.add(self.city)
        if capital or not self.owner.capital or len(self.owner.cities) > 0:
            self.owner.capital = self.city
        self._render_default_terrain()

    def get_cords(self) -> Tuple[float, float, float]:
        return self.pos_x, self.pos_y, self.pos_z

    def enrich_from_extra_data(self, hex: Hex) -> None:
        self.extra_data = hex  # type: ignore
        self.altitude = hex.altitude
        self.biome = hex.biome  # type: ignore
        self.moisture = hex.moisture
        self.temperature = hex.base_temperature[0]
        self.terrain = hex.terrain  # type: ignore
        self.zone = hex.zone.name  # type: ignore
        self.hemisphere = hex.hemisphere.name
        self.resource = hex.resource
        self.is_coast = hex.is_coast
        self.is_water = hex.is_water
        self.is_land = hex.is_land
        self.is_sea = hex.geoform_type.id == 2  # type: ignore # 2 == Sea
        self.is_lake = hex.geoform_type.id == 4  # type: ignore # 4 == Lake

    def destroy(self):
        self._entity_manager.unregister(entity=self, type=EntityType.TILE)
        self.unrender_all()
        self.destroyed = True
