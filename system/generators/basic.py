import random
from typing import TYPE_CHECKING, Dict, List, Type

from gameplay.resource import BaseResource, ResourceSpawnablePlace
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.tiles.base_tile import BaseTile
from system.generators.base import BaseGenerator
from system.pyload import PyLoad
from system.subsystems.hexgen.enums import MapType, OceanType, SuperEnum
from system.subsystems.hexgen.hex import Hex
from system.subsystems.hexgen.mapgen import MapGen

if TYPE_CHECKING:
    from system.game_settings import GameSettings


class HexResourceRating(SuperEnum):
    """((1 + 1) * 60/1000 ) / (60 ^ 2) * 10000"""

    __keys__ = ["id", "title", "rarity", "multiplier"]

    poor = (1, "Poor", 10, 4)
    average = (2, "Average", 6, 3)
    rich = (3, "Rich", 3, 2)
    abundant = (4, "Abundant", 1, 1)


class HexResourceType(SuperEnum):
    __keys__ = ["id", "rarity", "title", "material", "yield", "color"]

    iron_vein = (1, 15, "Iron Vein", 1000, "commonmetals", (100, 0, 0))
    copper_vein = (2, 15, "Copper Vein", 1000, "commonmetals", (0, 100, 0))
    silver_vein = (3, 15, "Silver Vein", 1000, "commonmetals", (0, 0, 100))
    lead_vein = (4, 15, "Lead Vein", 1000, "commonmetals", (100, 0, 100))
    aluminum_vein = (5, 15, "Aluminum Vein", 1000, "commonmetals", (50, 150, 50))
    tin_vein = (6, 15, "Tin Vein", 1000, "commonmetals", (150, 50, 50))
    titanium_vein = (7, 15, "Titanium Vein", 1000, "commonmetals", (200, 50, 200))
    magnesium_vein = (8, 15, "Magnesium Vein", 1000, "commonmetals", (50, 200, 50))

    gold_ore_deposit = (9, 1, "Gold Ore Deposit", 500, "preciousmetals", (255, 0, 0))
    chromite_ore_deposit = (
        10,
        3,
        "Chromite Ore Deposit",
        500,
        "preciousmetals",
        (255, 255, 0),
    )
    monazite_ore_deposit = (
        11,
        5,
        "Monazite Ore Deposit",
        500,
        "preciousmetals",
        (0, 0, 255),
    )
    bastnasite_ore_deposit = (
        12,
        4,
        "Bastnasite Ore Deposit",
        500,
        "preciousmetals",
        (0, 125, 200),
    )
    xenotime_ore_deposit = (
        13,
        1,
        "Xenotime Ore Deposit",
        500,
        "preciousmetals",
        (200, 125, 0),
    )

    graphite_deposit = (14, 10, "Graphite Deposit", 1500, "carbon", (0, 0, 0))
    coal_deposit = (15, 30, "Coal Deposit", 1500, "carbon", (255, 255, 255))

    quartz_deposit = (16, 7, "Quartz Vein", 1000, "silicon", (80, 80, 80))

    uranium_ore_deposit = (17, 1, "Uranium Ore Deposit", 10, "uranium", (255, 50, 50))


class Basic(BaseGenerator):
    NAME = "CivLike"
    DESCRIPTION = "Generates a hex-based map using HexGen."

    def __init__(self, config: "GameSettings", base):
        super().__init__(config, base=base)
        self.config: "GameSettings" = config
        self.map: Dict[str, BaseTile] = self.world.map
        from random import randrange

        # Random seed
        self.seed = randrange(0, 999999)

        # Load tile definitions
        self.tiles_dict: Dict[str, Type[BaseTile]] = self.load_tiles()

        # Initialize HexGen world parameters
        self.map_params = {
            "map_type": MapType.terran,
            "size": max(self.config.width, self.config.height),
            "random_seed": self.seed,
            "sea_percent": 40,  # 60% water coverage
            "ocean_type": OceanType.water,
            "roughness": 12,  # Controls terrain roughness
            "hydrosphere": True,  # Enables rivers/lakes
            "num_rivers": 50,  # Number of rivers
        }
        self.map_params = {
            "map_type": MapType.terran,
            "surface_pressure": 1013.25,
            "size": max(self.config.width, self.config.height),
            "year_length": 365,
            "day_length": 24,
            "base_temp": 0,
            "avg_temp": 12,
            "sea_percent": 55,
            "hydrosphere": True,
            "ocean_type": [OceanType.water, OceanType.hydrocarbons],
            "random_seed": self.seed,
            "roughness": 18,
            "height_range": (0, 245),
            "pressure": 1,  # bar
            "axial_tilt": 18,  # This is the most important part of temperature its temperature range in degrees dont go over like 30 for a very hot map 10 for a cold map 18 is earth about
            # features
            "craters": True,
            "volanoes": True,
            "num_rivers": 50,
            # territories
            "num_territories": 0,
        }

    def load_tiles(self) -> Dict[str, Type[BaseTile]]:
        """Loads tile classes dynamically."""
        classes = PyLoad.load_classes("gameplay/tiles", base_classes=BaseTile)
        # Remove the base class from the list
        if "BaseTile" in classes:
            del classes["BaseTile"]
        return classes

    def generate(self) -> bool:
        """Generates the hex map using HexGen and maps it to our tile system."""
        # Step 1: Generate the world using HexGen
        self.hexgen_map = MapGen(self.map_params, debug=True)
        self.hex_grid = self.hexgen_map.hex_grid  # Access HexGen's grid

        # Step 2: Convert HexGen's terrain types to our tile names and apply offsets
        for col in range(self.config.height):
            for row in range(self.config.width):
                # Compute the base x, y positions
                x = col * self.world.col_spacing  # Horizontal spacing

                if col % 2 == 1:  # Odd columns are staggered
                    y = row * self.world.row_spacing + (self.world.row_spacing * 0.5)
                else:
                    y = row * self.world.row_spacing  # Even columns align normally

                # Fetch the corresponding hex tile
                hex_tile = self.hex_grid.grid[col][row]

                # Convert HexGen biome to our tile system
                terrain = self.classify_terrain(hex_tile)
                hex_tile.terrain = terrain  # Store terrain type
                hex_tile.render_pos = (x, y)  # Store adjusted render coordinates

        # Step 4: Instantiate tiles for rendering
        self.instantiate_tiles()

        # Step 5: Place starting units
        self.place_starting_units()
        return True

    def classify_terrain(self, hex_tile) -> str:
        # arctic =               (1, 'a', 'Arctic')
        # tundra =               (2, 'u', 'Tundra')
        # alpine_tundra =        (3, 'p', 'Alpine Tundra')
        # desert =               (4, 'd', 'Desert')
        # shrubland =            (5, 's', 'Shrubland')
        # savanna =              (6, 'S', 'Savanna')
        # grasslands =           (7, 'g', 'Grasslands')
        # boreal_forest =        (8, 'b', 'Boreal Forest')
        # temperate_forest =     (9, 't', 'Temperate Forest')
        # temperate_rainforest = (10, 'T', 'Temperate Rainforest')
        # tropical_forest =      (11, 'r', 'Tropical Forest')
        # tropical_rainforest =  (12, 'R', 'Tropical Rainforest')

        desert_temperature_threshold = 35
        moistoire_threshold_mangrove_jungle = 13
        light_jungle_temperature_threshold = 25
        cold_forrest_temperature_threshold = 3

        if hex_tile.is_water:
            if hex_tile.biome.id in (2,) or hex_tile.temperature[0] < -1:
                return "SeaIce"

            elif (
                hex_tile.biome.id in (4, 7) and hex_tile.is_coast
            ):  # Shallow water, For some reason water is dessert or grassland
                return "Coast"
            elif hex_tile.geoform_type.id == 2:
                return "Lake"
            else:
                return "Sea"
        else:
            # Its land

            # We ask for the altitude to determine if it's a mountain
            if hex_tile.altitude > 205:
                if hex_tile.temperature[0] < -2:
                    return "MountainSnow"
                return "Mountain"

            if hex_tile.altitude > 165:
                if hex_tile.biome.id in (7,):
                    return "HillsGrassland"
                elif hex_tile.biome.id in (6, 4):
                    return "HillsDesert"
                elif hex_tile.biome.id in (3,):
                    return "HillsSnow"

            if (
                hex_tile.biome.id in (4,) and hex_tile.temperature[0] > desert_temperature_threshold
            ):  # Dessert or savannah, keep this high as it needs to be checked first before grassland
                return "FlatDesert"
            elif (
                hex_tile.biome.id in (7, 11) and hex_tile.moisture > moistoire_threshold_mangrove_jungle
            ):  # Virtual Mangrove Actual grassland with high moister
                return "FlatJungle"
            elif hex_tile.biome.id in (11,) and hex_tile.temperature[0] < light_jungle_temperature_threshold:
                return "FlatLightJungle"
            elif hex_tile.biome.id in (5,):  # Virtual Mangrove Actual scrubland with low moister
                return "FlatSchrubland"
            elif hex_tile.biome.id in (6,):  # Savana
                return "FlatSavanna"
            elif hex_tile.biome.id in (7,) or (
                hex_tile.biome.id in (6, 4) and hex_tile.temperature[0] <= desert_temperature_threshold
            ):  # Grassland and when its a "dessert" but to cold to be a dessert
                return "FlatGrass"
            elif hex_tile.biome.id in (
                8,
                12,
            ):  # flat heavy forrest virtual (cold boreal forest)
                if hex_tile.temperature[0] < cold_forrest_temperature_threshold:
                    return "FlatPineForest"
                return "FlatHeavyForest"
            elif hex_tile.biome.id in (12,):  # Fake tile type: Jungle not (Tropical Rainforest)
                pass
                # return "FlatJungle"
            elif hex_tile.biome.id in (
                11,
                10,
                9,
                8,
            ):  # forest
                return "FlatForrest"

            elif hex_tile.biome.id in (5,):  # Shrubland
                return "FlatSchrubland"
            elif hex_tile.biome.id in (1,):  # Arctic / Ice
                return "FlatIce"
            elif hex_tile.biome.id in (2, 3):  # 2 Tundra, 3 Alpine Tundra
                if hex_tile.temperature[0] < 0 or hex_tile.biome.id in (3,):  # This is a cold tile or alpine
                    return "FlatTundraSnow"
                return "FlatTundra"  # This is a normal tundra should be just 2 left as 3 is handled above
            elif hex_tile.biome.id in (13,):  # Wasteland
                return "FlatWasteland"

        raise ValueError(f"Terrain not found for hex_tile: {hex_tile}{hex_tile.biome}")

    def instantiate_tiles(self):
        """Creates Tile objects and places them on the grid."""
        for col in range(self.config.height):
            for row in range(self.config.width):
                hex_tile = self.hex_grid.grid[col][row]

                x, y = hex_tile.x, hex_tile.y
                terrain = hex_tile.terrain
                # Find the correct tile class or default to FlatGrassland
                tile_class = self.tiles_dict.get(terrain, self.tiles_dict.get("FlatGrassland"))
                if tile_class is None:
                    raise ValueError(f"Tile class for terrain '{terrain}' not found.")

                # Compute the rendering position using the correct offset
                render_x = col * self.world.col_spacing  # Base X spacing
                if col % 2 == 1:  # If the column is odd, apply staggered row offset
                    render_y = row * self.world.row_spacing + (self.world.row_spacing * 0.5)
                else:
                    render_y = row * self.world.row_spacing  # Even columns align normally

                # Instantiate the tile object
                obj_instance: BaseTile = tile_class(self.base, x, y, render_x, render_y, extra_data=hex_tile)
                obj_instance.register()

                def inject_resource():
                    self.choose_resource(obj_instance, hex_tile)
                    return obj_instance

                inject_resource()

                obj_instance.enrich_from_extra_data(hex=hex_tile)
                obj_instance.render()
                obj_instance.add_data_to_tileyield()

                # Generate a unique tag for mapping
                tag = obj_instance.generate_tag(x, y)
                self.map[tag] = obj_instance
                self.world.grid[(col, row)] = obj_instance

    def get_all_resources(self) -> List[Type[BaseResource]]:
        from gameplay.repositories.resources import ResourceRepository
        from gameplay.resource import ResourceType

        instance = ResourceRepository()
        resources = instance.all_by_type([ResourceType.STRATEGIC, ResourceType.BONUS, ResourceType.LUXURY])
        return resources

    def choose_resource(self, _base_tile: BaseTile, hex_tile: Hex) -> Type[BaseResource] | None:
        """@TODO add stats for the map to show how % of each resource is on the map and what type and average spawn rates"""
        all_resources: List[Type[BaseResource]] = self.get_all_resources()
        hex_tile = hex_tile

        def _choose_resource() -> Type[BaseResource] | None:
            filtered_resource: Type[BaseResource] | None = filter_out_tile_specific_resources(all_resources, _base_tile)
            return filtered_resource

        def filter_out_tile_specific_resources(
            _all_resources: List[Type[BaseResource]], base_tile: BaseTile
        ) -> Type[BaseResource] | None:
            """
            Returns a single resource from 'available_resources' that is valid for the given tile.
            Returns None if no valid resource can be found after 100 attempts.
            """
            i = 0
            while i < 100:
                resource: Type[BaseResource] = random.choice(_all_resources)
                i += 1

                def filter_by_type() -> bool:
                    # If the tile is water, skip land-only resources
                    if resource.spawn_type == ResourceSpawnablePlace.BOTH:
                        return True
                    elif (
                        (hex_tile.is_water and not hex_tile.is_land)
                        and (resource.spawn_type is ResourceSpawnablePlace.LAND)
                    ) or (
                        (hex_tile.is_land and not hex_tile.is_water)
                        and (resource.spawn_type is ResourceSpawnablePlace.WATER)
                    ):
                        return False
                    elif (
                        base_tile.get_terrain().can_spawn_resources is False
                    ):  # to prevent things like mountains spawning resources
                        return False
                    elif hex_tile.temperature[0] < -1.0 and hex_tile.is_water is True:
                        return False  # No resources on sea ice # Land based can spawn due to migration
                    elif (hex_tile.is_water is False and hex_tile.is_land is False) and (
                        resource.spawn_type is ResourceSpawnablePlace.LAND
                    ):  # Think hexgen has a bug with plains @TODO check this
                        return True
                    return True

                def filter_by_terrain() -> bool:
                    # If the resource requires a specific terrain type, check if it matches
                    if isinstance(resource.spawn_chance, dict):
                        if (
                            base_tile.get_terrain().__class__ not in resource.spawn_chance
                            and BaseTerrain not in resource.spawn_chance
                        ):
                            return False

                    return True

                if filter_by_type() is False:
                    continue
                if filter_by_terrain() is False:
                    continue

                # If we get here, the resource is valid for the tile
                return resource
            # If we couldn't find a valid resource in 100 tries, return None
            return None

        resource: Type[BaseResource] | None = _choose_resource()

        if resource is None:
            spawn_chance: float = 0.0  # @TODO add a default spawn chance for resources that are not found, This is to prevent mountains from spawning resources

        # Determine the spawn chance for the resource
        spawn_chance = getattr(resource, "spawn_chance", 0.0)
        filtered_spawn_chance: float = 0.0
        if isinstance(spawn_chance, dict):
            terrain = _base_tile.get_terrain()
            terrain_type = terrain.__class__
            if isinstance(spawn_chance, dict) and terrain_type in spawn_chance:
                filtered_spawn_chance: float = spawn_chance.get(
                    terrain_type, spawn_chance.get(BaseTerrain, 0.0)
                )  # base terrain is the default, if it doesn't exist then 0, so you can define to not spawn on a specific terrain.
            else:
                filtered_spawn_chance: float = 0.0
        elif isinstance(spawn_chance, float) or isinstance(spawn_chance, int):
            filtered_spawn_chance: float = spawn_chance
        else:
            raise ValueError(f"Invalid spawn_chance type for resource {resource}")

        # Attempt to place the resource on the tile based on its spawn chance
        against_chance = random.uniform(0, 100)  # for profiler it makes it easier to see the random call
        if float(against_chance) <= float(filtered_spawn_chance):
            if resource is not None:
                hex_tile.add_gameplay_resource(resource)  # Assign the resource to the tile
                # used_resources.add(resource)  # Track used resources to increase variety

                # If the resource is clusterable, attempt clustering
                if resource.clusterable is not None:
                    self._cluster_resource(hex_tile, resource)

    def _cluster_resource(self, center_tile, resource):
        """
        Handles clustering of resources around the initially placed tile.
        """

        # Determine maximum cluster radius and dropoff rate
        max_radius = (
            resource.cluster_max_radius
            if isinstance(resource.cluster_max_radius, int)
            else random.randint(resource.cluster_max_radius[0], resource.cluster_max_radius[1])
        )
        dropoff_rate = (
            resource.cluster_dropoff_amount_rate
            if isinstance(resource.cluster_dropoff_amount_rate, float)
            else random.uniform(resource.cluster_dropoff_amount_rate[0], resource.cluster_dropoff_amount_rate[1])
        )

        # Use bubble function to get all hexes within clusterable radius
        cluster_hexes = center_tile.bubble(max_radius)

        for hex_tile in cluster_hexes:
            if hex_tile.resource is None:
                # Compute probability based on distance from original tile
                distance = self._hex_distance(center_tile, hex_tile)
                new_probability = 1.0 - (dropoff_rate * distance)

                # Ensure probability is above zero before proceeding
                if new_probability > 0 and random.uniform(0, 1) <= new_probability * resource.clusterable:
                    hex_tile.resource = resource  # Assign resource to neighboring tile

    def _hex_distance(self, hex1, hex2):
        """
        Calculates the distance between two hex tiles using axial coordinates.
        """
        dx = abs(hex1.x - hex2.x)
        dy = abs(hex1.y - hex2.y)
        return max(dx, dy, abs(dx - dy))
