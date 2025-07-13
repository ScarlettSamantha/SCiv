import math
import weakref
from dataclasses import dataclass, field
from enum import Enum
from logging import Logger
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Set, Tuple, Type, Union, cast

from direct.showbase import MessengerGlobal
from direct.showbase.MessengerGlobal import messenger
from gameplay._units import Units
from gameplay.condition import Conditions
from gameplay.improvements_set import ImprovementsSet
from gameplay.player import Player
from gameplay.repositories.tile import TileRepository
from gameplay.resource import BaseResource, Resources
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.yields import Yields
from helpers.cache import Cache
from helpers.colors import Tuple4f
from helpers.maths import scale_value, scaled_pos_z
from managers.entity import EntityManager, EntityType
from managers.i18n import T_TranslationOrStr
from managers.player import PlayerManager
from panda3d.core import (
    LRGBColor,
    NodePath,
)
from system.effects import Effects
from system.entity import BaseEntity
from system.mesh import HexGrid
from system.subsystems.hexgen.edge import Edge
from system.subsystems.hexgen.enums import Biome, GeoformType, HexFeature
from system.tile_render import TileRenderer

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


default_slots = {
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


@dataclass(init=False, eq=False, unsafe_hash=False)
class Tile(BaseEntity):
    HEMISPHERE_UNKNOWN: int = 0b00000000
    HEMISPHERE_NORTH: int = 0b00000001
    HEMISPHERE_SOUTH: int = 0b00000010

    _prop_slots: Dict[str, Tuple[float, float, float]] = field(
        default_factory=lambda: {k: (v[0], v[1], float(v[2])) for k, v in default_slots.items()}, repr=False
    )
    z_scale: float = 1.75

    x: int = 0
    y: int = 0
    pos_x: float = 0.0
    pos_y: float = 0.0
    pos_z: float = 0.0

    tag: str = field(init=False)
    player: "Player | None" = field(default=None, repr=False)
    city: "City | None" = field(default=None, repr=False)
    city_owner: "City | None" = field(default=None, repr=False)
    _entity_manager: EntityManager = field(init=False, repr=False)
    logger: Logger = field(init=False, repr=False)
    renderer: TileRenderer = field(init=False, repr=False)
    effects: Effects = field(init=False, repr=False)
    resources: Resources = field(default_factory=Resources, repr=False)
    units: Units = field(default_factory=Units, repr=False)

    _improvements: ImprovementsSet = field(init=False, repr=False)
    _tile_terrain: BaseTerrain = field(init=False, repr=False)
    _features: Set["HexFeature | None"] = cast("Set[HexFeature | None]", field(default_factory=set, repr=False))
    _geoforms: GeoformType | None = field(default=None, repr=False)
    _edges: Dict[str, Union[weakref.ReferenceType["Edge"], "Edge", None]] = field(
        default_factory=lambda: {
            "n": None,
            "ne": None,
            "se": None,
            "s": None,
            "sw": None,
            "nw": None,
        },
        repr=False,
    )

    destroyed: bool = False
    is_water: bool = False
    is_land: bool = False
    is_sea: bool = False
    is_lake: bool = False
    is_coast: bool = False

    altitude: float = 0.0
    hemisphere: int = HEMISPHERE_UNKNOWN
    temperature: float = 0.0
    moisture: float = 0.0
    inherit_passability_from_terrain: bool = True
    coast_directions: Set[int] = cast(Set[int], field(default_factory=set))
    biome: int = 0
    _biome: Any = field(default=None, repr=False)
    passable: bool = True
    passable_without_tech: bool = True
    walkable: bool = True
    climbable: bool = True
    block_resource_model_spawning: bool = False
    needs_tile_proecessing: bool = True

    tile_yield: Yields = field(
        default_factory=lambda: Yields(
            gold=0.0, production=1.0, science=0.0, food=1.0, culture=0.0, housing=0.0, mode=Yields.BASE
        )
    )

    visible_sides: Dict[int, bool] = field(default_factory=lambda: {i: True for i in range(6)})
    is_selected: bool = False

    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        pos_x: float = 0.0,
        pos_y: float = 0.0,
        pos_z: float = 0.0,
    ) -> None:
        super().__init__(tile=weakref.ref(self))

        self.entity_type_ref = EntityType.TILE.value
        self.x = x
        self.y = y
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.pos_z = pos_z

        self.tag = self.generate_tag()

        self.__post_init__()

    def __post_init__(self) -> None:
        self._entity_manager = EntityManager.get_singleton_instance()
        self.logger = self.base.logger.gameplay.getChild("map.tile")

        self._prop_slots = {k: (float(v[0]), float(v[1]), float(v[2])) for k, v in default_slots.items()}
        self._edges = {
            "n": None,
            "ne": None,
            "se": None,
            "s": None,
            "sw": None,
            "nw": None,
        }

        self.z_scale = 1.75
        self.hpr: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.destroyed = False
        self.is_water = False
        self.is_land = False
        self.is_sea = False
        self.is_lake = False
        self.is_coast = False

        self.resources = Resources()
        self.units = Units()
        self.tile_yield = Yields(
            gold=0.0, production=1.0, science=0.0, food=1.0, culture=0.0, housing=0.0, mode=Yields.BASE
        )
        self.passable = True
        self.passable_without_tech = True
        self.walkable = True
        self.climbable = True
        self.tile_terrain = BaseTerrain()

        self.altitude = 0.0
        self.hemisphere = Tile.HEMISPHERE_UNKNOWN
        self.temperature = 0.0
        self.moisture = 0.0
        self.inherit_passability_from_terrain = True
        self.coast_directions = set()
        self.biome = 0
        self._improvements = ImprovementsSet()
        self._features = set()
        self._geoforms = None

        self.meshCollider = True
        self.is_selected = False

        if hasattr(self, "_tile_terrain"):
            self.tile_terrain = self._tile_terrain

        self.visible_sides = getattr(self, "visible_sides", {i: True for i in range(6)})
        self.tag = f"tile_{self.x}_{self.y}"
        self._entity_manager = EntityManager.get_singleton_instance()
        self.logger = self.base.logger.gameplay.getChild("map.tile")
        self.renderer = TileRenderer(self)
        self.effects = Effects(self)

        self.block_resource_model_spawning = False
        self.needs_tile_proecessing = True

        # register in the world
        self._entity_manager.register(EntityType.TILE, self, self.tag)

    def dump(self) -> Dict[str, Any]:
        data = self.__dict__.copy()
        data["_tile_terrain"] = self.tile_terrain.dump()
        data["biome"] = self._biome.id if self._biome else 0
        data["visible_sides"] = self._calculate_visible_sides()
        data["is"] = self._calculate_is_flags()
        data["_features"] = [feature.value if feature else None for feature in self.features]
        data["_edges"] = {
            side: edge() if isinstance(edge, weakref.ReferenceType) else None for side, edge in self.edges.items()
        }
        data["pos_x"], data["pos_y"], data["pos_z"] = round(self.pos_x, 3), round(self.pos_y, 3), round(self.pos_z, 3)
        data["effects"] = self.effects.dump()
        data["_improvements"] = self._improvements.dump()
        data["resources"] = self.resources.dump()
        data["units"] = self.units.dump()
        data["owner"] = self.get_owner().get_tag() if self._owner else None
        data["city"] = self.city.get_tag() if self.city else None
        for key in [
            "_entity_manager",
            "base",
            "logger",
            "renderer",
            "tile_yield",  # we don't want to dump the tile yield here, as it is calculated.
            "is_selected",
            "is_water",
            "is_land",
            "is_sea",
            "is_lake",
            "is_coast",
            "destroyed",
            "edges",
            "_biome",
            "visible_sides",
        ]:
            data.pop(key, None)
        return data

    def load_state(self) -> None:
        self.base = Cache.get_showbase_instance()
        self.logger = self.base.logger.gameplay.getChild("map.tile")
        self._entity_manager = EntityManager.get_singleton_instance()

        terrain_type: Dict[str, Any] = self._tile_terrain  # type: ignore
        if terrain_type:
            import_path: str | None = terrain_type.get("cls_ref", None)
            assert import_path is not None, "Terrain class reference is missing in state."
            terrain_class: Type[Any] = cast(
                Type[BaseTerrain], EntityManager.get_singleton_instance().dynamic_import(import_path=import_path)
            )
            self.tile_terrain = terrain_class()
            self.tile_terrain.load_state(terrain_type)

        resources = Resources()
        resources.load_state(self.resources)  # type: ignore
        self.resources = resources

        self._prop_slots = {k: (float(v[0]), float(v[1]), float(v[2])) for k, v in default_slots.items()}

        improvements = ImprovementsSet()
        improvements.load_state(self._improvements)  # type: ignore
        self._improvements = improvements

        effects = Effects(self)
        effects.load_state(self.effects)  # type: ignore
        self.effects = effects

        units = Units()
        units.load_state(self.units)  # type: ignore
        self.units = units

        self._from_is_flags(getattr(self, "is", 0))

        if self._owner is not None and isinstance(self._owner, str):
            _owner_instance_ref: weakref.ReferenceType[Player] | None = cast(
                weakref.ReferenceType["Player"] | None,
                self._entity_manager.get_ref_weak(EntityType.PLAYER, self._owner),
            )

        features: List[str] = getattr(self, "_features", [])
        if features:
            self._features = set()
            for _feature in features:
                feature: HexFeature | None = HexFeature.from_name(_feature)  # type: ignore
                if feature is not None:
                    assert isinstance(feature, HexFeature), "Feature must be of type HexFeature."
                    self._features.add(feature)

        if self._geoforms is not None:
            geoform_type: GeoformType | None = GeoformType.from_id(self._geoforms)  # type: ignore
            if geoform_type is not None:
                self._geoforms = geoform_type

        if self._biome is not None:
            biome_id: int = getattr(self, "biome", 0)
            self._biome = Biome.from_id(biome_id) if biome_id else None

        if self.city:
            city_ref: weakref.ReferenceType["City"] | None = cast(
                weakref.ReferenceType["City"] | None,
                self._entity_manager.get_ref_weak(EntityType.CITY, getattr(self, "city")),
            )
            if city_ref is not None:
                self.city = city_ref()

        self.renderer = TileRenderer(self)
        self.render()

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

    def __hash__(self) -> int:
        return hash(self.tag)

    @property
    def movement_cost(self) -> float:
        return 1 * self.tile_terrain.movement_modifier

    @property
    def features(self) -> Set[Any]:
        return self._features

    @features.setter
    def features(self, value: Set["HexFeature | None"]) -> None:
        if len(value) > 0:
            self._features = set()
            for feature in value:
                if isinstance(feature, HexFeature):
                    self._features.add(feature)

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

    def get_prop_slots(self) -> Dict[str, Tuple[float, float, float]]:
        return self._prop_slots

    def __getstate__(self) -> Dict[str, Any]:
        state = self.__dict__.copy()

        edges = {}
        for side, edge in self.edges.items():
            if isinstance(edge, weakref.ReferenceType):
                _edge: Edge | None = edge()
                if _edge is None:
                    edges[side] = None
                else:
                    edges[side] = id(_edge)
            elif edge is not None:
                edges[side] = edge

        state["edges"] = edges
        state["improvements"] = self._improvements.__getstate__()
        state["resources"] = self.resources.__getstate__()
        state["units"] = [unit.get_tag() for unit in self.units.all()]
        state["tile_yield"] = self.tile_yield.dump()
        state["features"] = [feature.name for feature in self.features]
        state["biome"] = self._biome.id
        state["pos_x"] = round(self.pos_x, 4)
        state["pos_y"] = round(self.pos_y, 4)
        state["pos_z"] = round(self.pos_z, 4)
        state["hpr"] = tuple(round(angle, 4) for angle in self.hpr)
        state["visible_sides"] = self._calculate_visible_sides()
        state["is"] = self._from_is_flags(state.get("is", 0))
        state.pop("base", None)
        state.pop("logger", None)
        state.pop("renderer", None)
        state.pop("_entity_manager", None)
        state.pop("effects", None)
        state.pop("_addTask", None)
        state.pop("_clearTask", None)
        state.pop("_improvements", None)
        state.pop("_tile_terrain", None)
        state.pop("_features", None)
        state.pop("_biome", None)
        state.pop("prop_slots", None)
        state.pop("is_selected", None)
        state.pop("destroyed", None)
        state.pop("is_coast", None)
        state.pop("is_water", None)
        state.pop("is_land", None)
        state.pop("is_sea", None)
        state.pop("is_lake", None)
        state.pop("_edges", None)
        state.pop("tile")
        return state

    def _calculate_is_flags(self) -> int:
        return (
            (1 if self.is_water else 0)
            | (2 if self.is_land else 0)
            | (4 if self.is_sea else 0)
            | (8 if self.is_lake else 0)
            | (16 if self.is_coast else 0)
        )

    def _from_is_flags(self, flags: int) -> None:
        self.is_water = bool(flags & 1)
        self.is_land = bool(flags & 2)
        self.is_sea = bool(flags & 4)
        self.is_lake = bool(flags & 8)
        self.is_coast = bool(flags & 16)

    def _calculate_visible_sides(self) -> int:
        return sum(1 << i for i, v in self.visible_sides.items() if v)

    def on_inspect(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        yields = self.tile_yield.on_inspect()

        render = {}
        render: Dict[str, str | int | float] = self.renderer.on_inspect()

        terrain = self.tile_terrain.on_inspect() if self.tile_terrain else {}

        data = {
            "tag": self.tag,
            "x, y": f"{self.x} , {self.y}",
            "pos": f"({self.pos_x}, {self.pos_y}, {self.pos_z})",
            "hpr": f"({self.hpr[0]}, {self.hpr[1]}, {self.hpr[2]})",
            "altitude": self.altitude,
            "terrain": self.tile_terrain.name if self.tile_terrain else None,
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
        return f"{self.tag}@{self.x},{self.y}"

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
        if auto_calculate:
            self.calculate()  # type: ignore
        self.renderer.render()

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
        yield_copy = self.tile_yield.get_copy()

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
        if unit.is_being_build:
            return

        self.units.add_unit(unit)
        if len(self.units) == 1:
            self.renderer.on_unit_enter()

    def remove_unit(self, unit: "Unit") -> None:
        if unit.is_being_build:
            return

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
