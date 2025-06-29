from copy import deepcopy
from enum import Enum
from logging import Logger
import math
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Set, Tuple, Type, Union, cast
import weakref

from helpers.colors import Tuple4f
from direct.showbase import MessengerGlobal
from direct.showbase.MessengerGlobal import messenger
from panda3d.core import (
    LRGBColor,
    NodePath,
)

from gameplay._units import Units
from gameplay.combat.damage import DamageMode
from gameplay.condition import Conditions
from gameplay.improvements_set import ImprovementsSet
from gameplay.repositories.tile import TileRepository
from gameplay.resource import BaseResource, Resources
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.weather import BaseWeather
from gameplay.yields import Yields
from helpers.cache import Cache
from helpers.maths import scale_value, scaled_pos_z
from managers.entity import EntityManager, EntityType
from managers.i18n import T_TranslationOrStr
from managers.player import PlayerManager
from system.effects import Effects
from system.entity import BaseEntity

from system.mesh import HexGrid
from system.subsystems.hexgen.enums import GeoformType
from system.subsystems.hexgen.edge import Edge
from system.tile_render import TileRenderer
from world.items._base_item import BaseItem


if TYPE_CHECKING:
    from gameplay.city import City
    from gameplay.improvement import Improvement
    from gameplay.unit import Unit
    from managers.player import Player
    from system.generators.basic import HexFeature


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

        self.is_coast: bool = False
        self.is_water: bool = False
        self.is_land: bool = False
        self.is_sea: bool = False
        self.is_lake: bool = False

        self.prop_size_scale_factor: float = 0.3
        self.prop_slots: Dict[str, Tuple[float, float, float]] = {
            "e": (0.45, 0.0, 0),
            "ne": (0.375, 0.35, 0),
            "nw": (-0.375, 0.35, 0),
            "w": (-0.45, 0.0, 0),
            "sw": (-0.375, -0.35, 0),
            "se": (0.375, -0.35, 0),
            "center": (0.0, 0.0, 0),
            "n": (0.0, 0.45, 0),
            "s": (0.0, -0.45, 0),
        }

        self._edges: Dict[str, Optional[Union[Edge, weakref.ReferenceType[Edge]]]] = {
            "e": None,
            "ne": None,
            "nw": None,
            "w": None,
            "sw": None,
            "se": None,
        }

        self.is_selected: bool = False

        self.altitude: float = 1

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

        self._features: Set[Any] = set()
        self._geoforms: Optional[GeoformType] = None
        self.biome: int = 1
        self.units: Units = Units()
        self._improvements: ImprovementsSet = ImprovementsSet()
        self.items: List[BaseItem] = list()
        self.states: List[Any] = []

        self.city: Optional["City"] = None
        self.city_owner: Optional["City"] = None

        self.claimants: List[Any] = []

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

        self.effects: Effects = Effects(self)
        self.needs_tile_proecessing: bool = False
        self.block_resource_model_spawning: bool = False
        self.visible_sides: Dict[int, bool] = {i: True for i in range(6)}

        self.renderer: TileRenderer = TileRenderer(self)

        self.register()

    @property
    def features(self) -> Set[Any]:
        return self._features

    @features.setter
    def features(self, value: Set["HexFeature | None"]) -> None:
        if len(value) > 0:
            self._features = value

    @property
    def geoforms(self) -> Optional[GeoformType]:
        return self._geoforms

    @geoforms.setter
    def geoforms(self, value: GeoformType) -> None:
        self._geoforms = value.value[0]

    @property
    def tile_terrain(self) -> BaseTerrain:
        return self._tile_terrain

    @tile_terrain.setter
    def tile_terrain(self, value: BaseTerrain) -> None:
        self._tile_terrain = value
        if self.inherit_passability_from_terrain:
            self.passable: bool = True if self.tile_terrain.passable is True else False
            self.passable_without_tech: bool = True if self.tile_terrain.passable_without_tech is True else False

    @property
    def edges(self) -> Dict[str, Union["Edge", None, weakref.ReferenceType["Edge"]]]:
        data: Dict[str, Union[weakref.ReferenceType["Edge"], "Edge", None]] = {}
        for side, edge in self._edges.items():
            if isinstance(edge, weakref.ReferenceType):
                data[side] = edge()
            else:
                data[side] = edge
        return data

    @edges.setter
    def edges(self, value: Dict[str, Optional[Union["Edge", weakref.ReferenceType["Edge"]]]]) -> None:
        if len(value) != 6:
            raise ValueError(f"Edges must have exactly 6 sides, got {len(value)}.")
        for side in value:
            if side not in self._edges:
                raise ValueError(f"Invalid edge side: {side}. Valid sides are: {list(self._edges.keys())}")
            if isinstance(value[side], Edge):
                self._edges[side] = weakref.ref(value[side])  # type: ignore
            elif value[side] is None:
                self._edges[side] = None
            elif isinstance(value[side], weakref.ReferenceType):
                self._edges[side] = value[side]
            else:
                raise TypeError(f"Invalid type for edge {side}: {type(value[side])}. Expected Edge or None.")

    def get_tile_terrain(self) -> BaseTerrain:
        return self._tile_terrain

    def get_edge(self, side: str) -> Optional["Edge"]:
        if side not in self.edges:
            raise ValueError(f"Invalid edge side: {side}. Valid sides are: {list(self.edges.keys())}")
        edge = self.edges[side]
        if isinstance(edge, weakref.ReferenceType):
            return edge()
        return edge

    def get_node(self) -> NodePath:
        return self.renderer.geometry_node

    def get_edges(self, as_reference: bool = True) -> Dict[str, Union["Edge", None, weakref.ReferenceType["Edge"]]]:
        data: Dict[str, Union[weakref.ReferenceType["Edge"], "Edge", None]] = {}
        for side, edge in self.edges.items():
            if isinstance(edge, weakref.ReferenceType) and not as_reference:
                edge = edge()
            elif isinstance(edge, Edge) and as_reference:
                edge = weakref.ref(edge)
            data[side] = edge
        return data

    def generate_tag(self) -> str:
        return f"tile_{self.x}_{self.y}"

    def on_load(self) -> None:
        self.register()

        self.base = Cache.get_showbase_instance()
        self.logger = self.base.logger.gameplay.getChild("map.tile")
        self.effects = Effects(self)

        self.renderer.render()
        self.pos_x, self.pos_y, self.pos_z = self.calculate_z_pos_on_altitude()

        if self.city is not None:
            self.city.base = self.base
            self.city.register()

    def calculate(self):
        new_yield = Yields.nullYield()

        base = self._tile_terrain.get_tile_yield()
        new_yield += base

        if self.is_city() and self.city is not None:
            city_yield = self.city.get_yield()
            new_yield += city_yield
        else:
            for improvement in self._improvements.get_all():
                new_yield += improvement.tile_yield

                for improvement_effect in improvement.effects.get_effects().values():
                    new_yield += improvement_effect.yield_impact

        for effect in self.effects.get_effects().values():
            new_yield += effect.yield_impact

        for resource in self.resources.flatten_non_mechanic().values():
            new_yield += resource.get_yield()

        self.tile_yield = new_yield

    def __getstate__(self) -> Dict[str, Any]:
        state = self.__dict__.copy()
        if "base" in state:
            del state["base"]
        if "logger" in state:
            del state["logger"]
        if "renderer" in state:
            del state["renderer"]
        if "_entity_manager" in state:
            del state["_entity_manager"]
        if "effects" in state:
            del state["effects"]
        if "_addTask" in state:
            del state["_addTask"]
        if "_clearTask" in state:
            del state["_clearTask"]
        state["tag"] = self.tag
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        self.__dict__.update(state)
        self.base = Cache.get_showbase_instance()
        self.logger = self.base.logger.gameplay.getChild("map.tile")
        self._entity_manager = EntityManager.get_singleton_instance()
        self.renderer = TileRenderer(self)
        self.effects = Effects(self)
        self.visible_sides = state.get("visible_sides", {i: True for i in range(6)})

        if "tile_yield" not in state:
            self.tile_yield = Yields.nullYield()

        if "effects" not in state:
            self.effects = Effects(self)

        for key, value in state.items():
            setattr(self, key, value)

    def on_inspect(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        yields = self.tile_yield.on_inspect()

        render = {}
        render: Dict[str, str | int | float] = self.renderer.on_inspect()

        terrain = self.tile_terrain.on_inspect() if self.tile_terrain else {}

        data = {
            "tag": self.tag,
            "id": self.id,
            "x, y": f"{self.x} , {self.y}",
            "pos": f"({self.pos_x}, {self.pos_y}, {self.pos_z})",
            "hpr": f"({self.hpr[0]}, {self.hpr[1]}, {self.hpr[2]})",
            "altitude": self.altitude,
            "terrain": self.tile_terrain.name if self.tile_terrain else None,
            "zone": self.zone,
            "hemisphere": self.hemisphere,
            "is_water": str(self.is_water),
            "is_land": str(self.is_land),
            "is_sea": str(self.is_sea),
            "is_lake": str(self.is_lake),
            "is_coast": str(self.is_coast),
            "is_city": self.is_city(),
            "city": self.city.tag if self.city else None,
            "city_owner": str(self.city_owner.tag) if self.city_owner else None,
            "owner": str(self.get_owner().name) if self.owner else "nature",
            "resources": self.resources.on_inspect(),
            "features": [feature.name for feature in self.features],
            "geoforms": str(self.geoforms) if self.geoforms else None,
            "biome": self.biome,
            "units": [unit.tag for unit in self.units.all()],
            "improvements": [improvement.tag for improvement in self._improvements.get_all()],
            "visible_sides": {side: "true" if edge else "false" for side, edge in self.visible_sides.items()},
            "moisture": self.moisture,
            "temperature": self.temperature,
        }
        data.update(yields)
        data.update(render)
        data.update(terrain)

        return (data, self.get_children_inspect())

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

    def get_improvements(self) -> ImprovementsSet:
        return self._improvements

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
        self._entity_manager.register(entity=self, key=str(self.tag), type=EntityType.TILE)

    def select(self) -> None:
        self.is_selected = True
        self.on_select()

    def deselect(self) -> None:
        self.is_selected = False
        self.renderer.toggle_tile_selector(False)

    def on_select(self) -> None:
        self.renderer.toggle_tile_selector(True)

    def unregister(self):
        self._entity_manager.unregister(entity=self, type=EntityType.TILE)

    def compute_hex_center(self, x: int, y: int, radius: float = 1) -> Tuple[float, float]:
        horizontal_spacing = 1.5 * radius
        vert = math.sqrt(3) * radius

        pos_x = x * horizontal_spacing
        pos_y = y * vert + (vert * 0.5 if (x % 2) else 0.0)

        return pos_x, pos_y

    def is_visisted_by(self, unit: "Unit") -> bool:
        messenger.send("unit.action.move.visiting_tile", [unit, self])
        self.logger.info(f"Unit {str(unit.tag)} is visiting tile {str(self.tag)}.")
        return True

    def get_distance(self, other: "Tile") -> int:
        return TileRepository.distance(self, other)

    def recalculate_grid_position(self, radius: float = 1) -> None:
        px, py = self.compute_hex_center(self.x, self.y, radius)
        self.pos_x, self.pos_y = px, py

    def set_walls_color(self, color: Tuple[float, ...]) -> None:
        from managers.game import Game

        mesh: HexGrid = Game.get_singleton_instance().get_mesh()
        mesh.set_wall_color_for_tile(mesh.get_tile_index_from_coords(self.x, self.y), cast(Tuple4f, color))

    def render(self, auto_calculate: bool = True) -> None:
        self.renderer.render(update_yields=auto_calculate)

    def on_turn_end(self, turn: int) -> None:
        if len(self._improvements) > 0:  # We only process improvements if we have any.
            self._improvements.on_turn_end(turn)

        if len(self.effects) > 0:
            self.effects.on_turn_end(turn)

        if len(self.units) > 0:
            for unit in self.units.all():
                unit.attack_points_left = unit.attack_points  # Reset attack points for the next turn

    def calculate_z_pos_on_altitude(self) -> Tuple[float, float, float]:
        pos_z = scale_value(min(self.altitude, 240), 44, 240, 0, 1.5)
        pos_z = scaled_pos_z(pos_z, 0, 0.75, self.z_scale)
        return (self.pos_x, self.pos_y, float(pos_z))

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
            and not self.is_lake
            and (on_other_units or len(self.units) == 0)
            and not self.city
            and (
                on_mountains or self.altitude < 200
            )  # No spawning on mountains # @TODO this might be a bug. check in the future if this is the reason units can spawn on mountains.
        )

    def is_passable(self) -> bool:
        if self.inherit_passability_from_terrain:
            return self.passable
        return self.walkable and not self.is_water and not self.is_sea and not self.is_lake and not self.is_coast

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
        if len(self.units) == 1:
            self.renderer.on_unit_enter()

    def remove_unit(self, unit: "Unit") -> None:
        # Assuming the intent is to remove the unit.
        self.units.remove_unit(unit)
        if len(self.units) == 0:
            self.renderer.on_unit_leave()

    def is_occupied(self) -> bool:
        return len(self.units._units) > 0 or self.city is not None  # type: ignore

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
        self.resources.add_improvement(improvement)
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
        self.resources.add(resource(3), auto_instance=True)

    def get_children_inspect(self) -> Dict[str, Set[Any] | List[Any]]:
        if self.city is not None:
            return {
                "units": set(self.units.all()),
                "improvements": set(self._improvements.get_all()),
                "effects": set(self.effects.get_effects().values()),
                "city": {self.city},
            }
        else:
            return {
                "units": set(self.units.all()),
                "improvements": set(self._improvements.get_all()),
                "effects": set(self.effects.get_effects().values()),
            }

    def destroy(self, as_system: bool = False) -> None:
        self.renderer.clear_ui()
        self.renderer.destroy()
        del self.renderer
        self.unregister()
        self.destroyed = True
        del self
