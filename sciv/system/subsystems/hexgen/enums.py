from enum import Enum
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
)

from system.subsystems.hexgen.constants import TERRAIN_TERRAN

T = TypeVar("T", bound="SuperEnum")


class SuperEnum(Enum):
    """
    Enum with dynamic fields. Each value is a tuple mapped to __keys__.
    """

    __keys__: ClassVar[List[str]] = []

    def __init__(self, *args: Any):
        for key, value in enumerate(args):
            for namekey, name in enumerate(self.__keys__):
                if key == namekey:
                    setattr(self, name, value)

    def to_dict(self) -> Dict[str, Any]:
        rep = {key: getattr(self, key) for key in self.__keys__}
        rep["name"] = self.name
        return rep

    def __getstate__(self) -> object:
        return super().__getstate__()

    @classmethod
    def get(cls: Type[T], id_: Any) -> Optional[T]:
        for item in cls:
            if getattr(item, "id", None) == id_:
                return item
        return None

    @classmethod
    def items(cls) -> List[str]:
        return list(cls.__members__)

    @classmethod
    def pluck(cls, key: str = "name") -> List[Any]:
        return [getattr(member, key) for member in cls]

    @classmethod
    def dump(cls) -> List[Dict[str, Any]]:
        return [member.to_dict() for member in cls]

    @classmethod
    def all(cls) -> List[Dict[str, Any]]:
        return cls.dump()

    @classmethod
    def members(cls) -> List[str]:
        return [member.name for member in cls]

    @classmethod
    def list(cls: Type[T]) -> List[T]:
        return list(cls)


# --- Enums ---


class Biome(SuperEnum):
    __keys__: ClassVar[List[str]] = ["id", "code", "title", "color", "base_fertility", "color_satellite"]

    lifeless = (13, "l", "Lifeless", (200, 200, 200), 0, (150, 150, 150))
    arctic = (1, "a", "Arctic", (224, 224, 224), 1, (132, 152, 159))
    tundra = (2, "u", "Tundra", (114, 153, 128), 15, (52, 55, 44))
    alpine_tundra = (3, "p", "Alpine Tundra", (97, 130, 106), 10, (59, 60, 42))
    desert = (4, "d", "Desert", (237, 217, 135), 5, (94, 78, 52))
    shrubland = (5, "s", "Shrubland", (194, 210, 136), 20, (58, 47, 21))
    savanna = (6, "S", "Savanna", (219, 230, 158), 80, (66, 53, 28))
    grasslands = (7, "g", "Grasslands", (166, 223, 106), 150, (45, 46, 22))
    boreal_forest = (8, "b", "Boreal Forest", (28, 94, 74), 30, (36, 41, 29))
    temperate_forest = (9, "t", "Temperate Forest", (76, 192, 0), 100, (40, 37, 19))
    temperate_rainforest = (10, "T", "Temperate Rainforest", (89, 129, 89), 100, (42, 38, 21))
    tropical_forest = (11, "r", "Tropical Forest", (96, 122, 34), 70, (32, 39, 21))
    tropical_rainforest = (12, "R", "Tropical Rainforest", (0, 70, 0), 60, (26, 33, 16))
    barren_dusty = (14, "bld", "Barren Drylands", (87, 26, 27), 0)
    barren = (16, "bld", "Barren Drylands", (43, 44, 35), 0)
    barren_wet = (21, "bw", "Barren Wetland", (77, 36, 37), 0, (22, 51, 61))
    barren_ice_caps = (18, "bi", "Barren Ice Caps", (242, 228, 216), 0)
    volcanic_liquid = (19, "mo", "Lava Fields", (217, 0, 0), 0)
    volcanic_molten_river = (19, "mo", "Lavaflow", (207, 10, 10), 0, (207, 10, 10))
    volcanic_solid = (20, "so", "Basaltic Plains", (40, 28, 25), 0)

    @classmethod
    def from_id(cls, id_: int) -> "Biome | None":
        for biome in cls.items():
            if biome.id == id_:
                return biome
        return None


class OceanType(SuperEnum):
    __keys__: ClassVar[List[str]] = ["id", "title"]
    water = (1, "Water")
    magma = (2, "Magma")
    hydrocarbons = (3, "Hydrocarbons")


class HexResourceRating(SuperEnum):
    __keys__: ClassVar[List[str]] = ["id", "title", "rarity", "multiplier"]
    poor = (1, "Poor", 10, 4)
    average = (2, "Average", 6, 3)
    rich = (3, "Rich", 3, 2)
    abundant = (4, "Abundant", 1, 1)


class HexResourceType(SuperEnum):
    __keys__: ClassVar[List[str]] = ["id", "rarity", "title", "material", "yield", "color"]
    iron_vein = (1, 15, "Iron Vein", 1000, "commonmetals", (100, 0, 0))
    copper_vein = (2, 15, "Copper Vein", 1000, "commonmetals", (0, 100, 0))
    silver_vein = (3, 15, "Silver Vein", 1000, "commonmetals", (0, 0, 100))
    lead_vein = (4, 15, "Lead Vein", 1000, "commonmetals", (100, 0, 100))
    aluminum_vein = (5, 15, "Aluminum Vein", 1000, "commonmetals", (50, 150, 50))
    tin_vein = (6, 15, "Tin Vein", 1000, "commonmetals", (150, 50, 50))
    titanium_vein = (7, 15, "Titanium Vein", 1000, "commonmetals", (200, 50, 200))
    magnesium_vein = (8, 15, "Magnesium Vein", 1000, "commonmetals", (50, 200, 50))
    gold_ore_deposit = (9, 1, "Gold Ore Deposit", 500, "preciousmetals", (255, 0, 0))
    chromite_ore_deposit = (10, 3, "Chromite Ore Deposit", 500, "preciousmetals", (255, 255, 0))
    monazite_ore_deposit = (11, 5, "Monazite Ore Deposit", 500, "preciousmetals", (0, 0, 255))
    bastnasite_ore_deposit = (12, 4, "Bastnasite Ore Deposit", 500, "preciousmetals", (0, 125, 200))
    xenotime_ore_deposit = (13, 1, "Xenotime Ore Deposit", 500, "preciousmetals", (200, 125, 0))
    graphite_deposit = (14, 10, "Graphite Deposit", 1500, "carbon", (0, 0, 0))
    coal_deposit = (15, 30, "Coal Deposit", 1500, "carbon", (255, 255, 255))
    quartz_deposit = (16, 7, "Quartz Vein", 1000, "silicon", (80, 80, 80))
    uranium_ore_deposit = (17, 1, "Uranium Ore Deposit", 10, "uranium", (255, 50, 50))


class HexEdge(SuperEnum):
    __keys__: ClassVar[List[str]] = ["id", "title", "short", "arrow"]
    east = (1, "East", "E", "→")
    north_east = (2, "North East", "NE", "↗")
    north_west = (3, "North West", "NW", "↖")
    west = (4, "West", "W", "←")
    south_west = (5, "South West", "SW", "↙")
    south_east = (6, "South East", "SE", "↘")


class MapType(SuperEnum):
    __keys__: ClassVar[List[str]] = ["id", "title", "colors"]
    terran = (1, "Terran", TERRAIN_TERRAN)
    gas = (3, "Gas", None)


class HexType(Enum):
    land = "Land"
    ocean = "Ocean"


class HexSurface(SuperEnum):
    __keys__: ClassVar[List[str]] = ["id", "specific_heat", "albedo"]
    water_fresh = (1, 1.00, 0.0)
    water_sea = (2, 0.94, 0.0)
    granite = (3, 0.19, 0.0)
    basalt = (4, 0.20, 0.0)
    soil_wet = (5, 0.35, 0.0)
    soil_dry = (6, 0.15, 0.0)
    soil_barren = (7, 0.10, 0.0)
    ice_warm = (8, 0.50, 0.0)
    ice_cold = (9, 0.40, 0.0)


class HexFeature(Enum):
    lake = "Lake"
    glacier = "Glacier"
    volcano = "Volcano"
    lava_flow = "Lava Flow"
    crater = "Crater"
    sea = "Sea"
    ocean = "Ocean"

    @classmethod
    def from_name(cls, name: str) -> Optional["HexFeature"]:
        for feature in HexFeature:
            if feature.name.lower() == name.lower():
                return feature
        return None


class GeoformType(SuperEnum):
    __keys__: ClassVar[List[str]] = ["id", "title", "color"]
    ocean = (1, "Ocean", (0, 0, 255))
    sea = (2, "Sea", (50, 50, 200))
    strait = (3, "Strait", (100, 100, 150))
    lake = (4, "Lake", (0, 0, 100))
    bay = (10, "Bay", (50, 50, 150))
    isthmus = (5, "Isthmus", (100, 150, 100))
    small_island = (6, "Small Island", (200, 255, 200))
    large_island = (7, "Large Island", (100, 255, 100))
    continent = (8, "Continent", (0, 255, 0))
    peninsula = (9, "Peninsula", (0, 200, 0))

    @classmethod
    def from_id(cls, id: int) -> Optional["GeoformType"]:
        for geoform in cls:
            if getattr(geoform, "id") == id:
                return geoform
        return None


class EdgeDirection(Enum):
    north = "North"
    south = "South"
    north_west = "North West"
    north_east = "North East"
    south_west = "South West"
    south_east = "South East"


class HexSide(Enum):
    east = "East"
    west = "West"
    north_west = "North West"
    north_east = "North East"
    south_west = "South West"
    south_east = "South East"

    def branching(self, direction: "EdgeDirection") -> tuple["HexSide", "HexSide"]:
        if self is HexSide.east or self is HexSide.west:
            if direction is EdgeDirection.north:
                return HexSide.south_west, HexSide.south_east
            else:
                return HexSide.north_west, HexSide.north_east
        elif self is HexSide.south_east:
            if direction is EdgeDirection.north_east:
                return HexSide.west, HexSide.south_west
            else:
                return HexSide.east, HexSide.north_east
        elif self is HexSide.south_west:
            if direction is EdgeDirection.north_west:
                return HexSide.east, HexSide.south_east
            else:
                return HexSide.west, HexSide.north_west
        elif self is HexSide.north_west:
            if direction is EdgeDirection.south_west:
                return HexSide.east, HexSide.north_east
            else:
                return HexSide.west, HexSide.south_west
        elif self is HexSide.north_east:
            if direction is EdgeDirection.north_west:
                return HexSide.east, HexSide.south_east
            else:
                return HexSide.north_west, HexSide.west
        raise Exception(f"Branching invalid, Side: {self}, Direction: {direction}")


class Zones(SuperEnum):
    __keys__: ClassVar[List[str]] = ["id", "title", "color", "map_key", "incr"]
    arctic_circle = (1, "Artic Circle", (150, 150, 250), "N", 0.60)
    northern_temperate = (2, "Northern Temperate", (150, 250, 150), "A", 0.90)
    northern_subtropics = (3, "Nothern Subtropics", (150, 250, 200), "B", 0.60)
    northern_tropics = (4, "Northern Tropics", (230, 150, 150), "C", 0.30)
    southern_tropics = (5, "Southern Tropics", (250, 180, 150), "D", 0.30)
    southern_subtropics = (6, "Southern Subtropics", (150, 250, 200), "E", 0.60)
    southern_temperate = (7, "Southern Temperate", (150, 250, 150), "F", 0.90)
    antarctic_circle = (8, "Antarctic Circle", (150, 150, 250), "S", 0.60)


class Hemisphere(Enum):
    northern = "Northern"
    southern = "Southern"


class Season(Enum):
    winter = "Winter"
    spring = "Spring"
    summer = "Summer"
    autumn = "Autumn"
