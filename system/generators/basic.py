from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Type

from gameplay.resource import BaseResource
from gameplay.tiles.base_tile import BaseTile
from system.generators.base import BaseGenerator
from system.generators.resource_allocator import ResourceAllocator
from system.pyload import PyLoad
from system.subsystems.hexgen.enums import MapType, OceanType
from system.subsystems.hexgen.mapgen import MapGen

if TYPE_CHECKING:
    from system.game_settings import GameSettings


class Basic(BaseGenerator):
    NAME = "CivLike"
    DESCRIPTION = "Generates a hex-based map using HexGen."

    def __init__(self, config: "GameSettings", base):
        super().__init__(config, base=base)
        self.config: "GameSettings" = config
        from random import randrange

        # Random seed
        self.seed = randrange(0, 999999)

        # Load tile definitions
        self.tiles_dict: Dict[str, Type[BaseTile]] = self.load_tiles()
        self.grid: Dict[Tuple[int, int], BaseTile] = {}
        self.map: Dict[str, BaseTile] = self.world.map

        self.resource_allocator: Optional[ResourceAllocator] = None

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
            "avg_temp": 10,
            "sea_percent": 55,
            "hydrosphere": True,
            "ocean_type": [OceanType.water, OceanType.hydrocarbons],
            "random_seed": self.seed,
            "roughness": 18,
            "height_range": (0, 240),
            "pressure": 1,  # bar
            "axial_tilt": 18,  # This is the most important part of temperature its temperature range in degrees dont go over like 30 for a very hot map 10 for a cold map 18 is earth about
            # features
            "craters": True,
            "volcanoes": True,
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

        # Step 5: Allocate resources
        self.grid = self.world.grid
        self.resource_allocator = ResourceAllocator(self.grid, self.get_all_resources())
        self.resource_allocator.allocate_resources()

        # Step 6: Place starting units
        self.place_starting_units()
        return True

    def classify_terrain(self, hex_tile) -> str:
        # arctic =               (1, 'a', 'Arctic')
        # tundra =               (2, 'u', 'Tundra')
        # alpine_tundra =        (3, 'p', 'Alpine Tundra')
        # desert =               (4, 'd', 'Desert')
        # scrubland =            (5, 's', 'Scrubland')
        # savanna =              (6, 'S', 'Savanna')
        # grasslands =           (7, 'g', 'Grasslands')
        # boreal_forest =        (8, 'b', 'Boreal Forest')
        # temperate_forest =     (9, 't', 'Temperate Forest')
        # temperate_rainforest = (10, 'T', 'Temperate Rainforest')
        # tropical_forest =      (11, 'r', 'Tropical Forest')
        # tropical_rainforest =  (12, 'R', 'Tropical Rainforest')

        desert_temperature_threshold = 30
        grass_temperature_upper_threshold = 30
        grass_temperature_lower_threshold = 10
        moisture_threshold_mangrove_jungle = 13
        light_jungle_temperature_threshold = 25
        cold_forrest_temperature_threshold = 3
        flat_to_hills_threshold = 160
        hills_to_mountains_threshold = 205

        if hex_tile.is_water:
            if hex_tile.biome.id in (2,) or hex_tile.temperature[0] < -1:
                return "SeaIce"

            elif (
                hex_tile.is_coast and hex_tile.geoform_type.id != 2
            ):  # Shallow water, For some reason water is dessert or grassland
                return "Coast"
            elif hex_tile.geoform_type.id == 2:
                return "Lake"
            else:
                return "Sea"
        else:
            # Its land
            # We ask for the altitude to determine if it's a mountain
            if hex_tile.altitude > hills_to_mountains_threshold:
                if hex_tile.temperature[0] < -2:
                    return "MountainSnow"
                return "Mountain"

            if hex_tile.altitude > flat_to_hills_threshold:
                if (
                    hex_tile.biome.id in (7, 5)
                    and hex_tile.temperature[0] > grass_temperature_lower_threshold
                    and hex_tile.temperature[0] < grass_temperature_upper_threshold
                ):
                    return "HillsGrassland"
                elif hex_tile.biome.id in (6, 4) and hex_tile.temperature[0] > desert_temperature_threshold:
                    return "HillsDesert"
                elif hex_tile.biome.id in (3,) and hex_tile.temperature[0] < 0:
                    return "HillsSnow"
                elif (
                    hex_tile.temperature[0] < grass_temperature_lower_threshold
                    and hex_tile.temperature[0] > 0
                    and hex_tile.biome.id not in (7, 5, 6, 4)
                ):
                    return "HillsTundra"

            if (
                hex_tile.biome.id in (4,) and hex_tile.temperature[0] > desert_temperature_threshold
            ):  # Dessert or savannah, keep this high as it needs to be checked first before grassland
                return "FlatDesert"
            elif (
                hex_tile.biome.id in (7, 11) and hex_tile.moisture > moisture_threshold_mangrove_jungle
            ):  # Virtual Mangrove Actual grassland with high moister
                return "FlatJungle"
            elif hex_tile.biome.id in (11,) and hex_tile.temperature[0] < light_jungle_temperature_threshold:
                return "FlatLightJungle"
            elif hex_tile.biome.id in (5,):  # Virtual Mangrove Actual scrubland with low moister
                return "FlatScrubland"
            elif hex_tile.biome.id in (6,):  # Savanna
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

            elif hex_tile.biome.id in (5,):  # Scrubland
                return "FlatScrubland"
            elif hex_tile.biome.id in (1,):  # Arctic / Ice
                return "FlatIce"
            elif hex_tile.biome.id in (2, 3) or (
                hex_tile.biome.id in (7, 6, 4) and hex_tile.temperature[0] < grass_temperature_lower_threshold
            ):  # 2 Tundra, 3 Alpine Tundra
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
                obj_instance: BaseTile = tile_class(x, y, render_x, render_y, extra_data=hex_tile)
                obj_instance.register()

                obj_instance.enrich_from_extra_data(hex=hex_tile)
                obj_instance.render()

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

    def _hex_distance(self, hex1, hex2):
        """
        Calculates the distance between two hex tiles using axial coordinates.
        """
        dx = abs(hex1.x - hex2.x)
        dy = abs(hex1.y - hex2.y)
        return max(dx, dy, abs(dx - dy))
