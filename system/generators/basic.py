import random
import re
from hexgen.grid import Grid
from hexgen.mapgen import MapGen
from hexgen.enums import MapType, OceanType
from data.tiles.tile import Tile
from system.generators.base import BaseGenerator
from system.pyload import PyLoad
from typing import TYPE_CHECKING, Dict, Type

if TYPE_CHECKING:
    from system.game_settings import GameSettings


class Basic(BaseGenerator):
    NAME = "CivLike"
    DESCRIPTION = "Generates a hex-based map using HexGen."

    def __init__(self, config: "GameSettings", base):
        super().__init__(config, base=base)
        self.config: "GameSettings" = config
        self.map: Dict[str, Tile] = self.world.map

        # Random seed
        self.seed = random.randint(0, 999999)

        # Load tile definitions
        self.tiles_dict: Dict[str, Type[Tile]] = self.load_tiles()

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

    def load_tiles(self) -> Dict[str, Type[Tile]]:
        """Loads tile classes dynamically."""
        classes = PyLoad.load_classes("data/tiles", base_classes=Tile)
        if "Tile" in classes:
            del classes["Tile"]
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

        # Step 3: Instantiate tiles for rendering
        self.instantiate_tiles()
        return True

    def classify_terrain(self, hex_tile) -> str:
        """Maps HexGen's terrain data to our tile names."""

        desert_temperature_threshold = 30
        moistoire_threshold_mangrove_jungle = 13
        light_jungle_temperature_threshold = 25

        if hex_tile.is_water:
            if hex_tile.biome.id in (2,) or hex_tile.temperature[0] < 0:
                return "SeaIce"

            elif (
                hex_tile.biome.id in (4, 7) and hex_tile.is_coast
            ):  # Shallow water, For some reason water is dessert or grassland
                return "Coast"
            else:
                return "Sea"
        else:
            # Its land

            # We ask for the altitude to determine if it's a mountain
            if hex_tile.altitude > 200:
                return "Mountain"
            if hex_tile.altitude > 160:
                if hex_tile.biome.id in (7,):
                    return "HillsGrassland"
                elif hex_tile.biome.id in (6, 4):
                    return "HillsDesert"

            if (
                hex_tile.biome.id in (4,)
                and hex_tile.temperature[0] > desert_temperature_threshold
            ):  # Dessert or savannah, keep this high as it needs to be checked first before grassland
                return "FlatDesert"
            elif (
                hex_tile.biome.id in (7, 11)
                and hex_tile.moisture > moistoire_threshold_mangrove_jungle
            ):  # Virtual Mangrove Actual grassland with high moister
                return "FlatJungle"
            elif (
                hex_tile.biome.id in (11,)
                and hex_tile.temperature[0] < light_jungle_temperature_threshold
            ):
                return "FlatLightJungle"
            elif hex_tile.biome.id in (
                5,
            ):  # Virtual Mangrove Actual scrubland with low moister
                return "FlatSchrubland"
            elif hex_tile.biome.id in (6,):  # Savana
                return "FlatSavanna"
            elif hex_tile.biome.id in (7,) or (
                hex_tile.biome.id in (6, 4)
                and hex_tile.temperature[0] <= desert_temperature_threshold
            ):  # Grassland and when its a "dessert" but to cold to be a dessert
                return "FlatGrass"
            elif hex_tile.biome.id in (
                8,
                12,
            ):  # flat heavy forrest virtual (cold boreal forest)
                return "FlatHeavyForest"
            elif hex_tile.biome.id in (
                12,
            ):  # Fake tile type: Jungle not (Tropical Rainforest)
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
            elif hex_tile.biome.id in (2,):  # Ice
                return "FlatTundra"
            elif hex_tile.biome.id in (1, 3):  # Arctic / Ice
                return "FlatSnow"
            elif hex_tile.biome.id in (13,):  # Wasteland
                return "FlatWasteland"

        raise ValueError(f"Terrain not found for hex_tile: {hex_tile}{hex_tile.biome}")

    def instantiate_tiles(self):
        """Creates Tile objects and places them on the grid."""
        for col in range(self.config.height):
            for row in range(self.config.width):
                hex_tile = self.hex_grid.grid[col][row]

                x, y = hex_tile.x, hex_tile.y  # ✅ Base HexGen coordinates
                terrain = hex_tile.terrain  # ✅ Now correctly assigned

                # Find the correct tile class or default to FlatGrassland
                tile_class = self.tiles_dict.get(
                    terrain, self.tiles_dict.get("FlatGrassland")
                )
                if tile_class is None:
                    raise ValueError(f"Tile class for terrain '{terrain}' not found.")

                # Compute the rendering position using the correct offset
                render_x = col * self.world.col_spacing  # Base X spacing
                if col % 2 == 1:  # If the column is odd, apply staggered row offset
                    render_y = row * self.world.row_spacing + (
                        self.world.row_spacing * 0.5
                    )
                else:
                    render_y = (
                        row * self.world.row_spacing
                    )  # Even columns align normally

                # Instantiate the tile object
                obj_instance: Tile = tile_class(
                    self.base, x, y, render_x, render_y, extra_data=hex_tile
                )
                obj_instance.render()

                # Generate a unique tag for mapping
                tag = obj_instance.generate_tag(x, y)
                self.map[tag] = obj_instance
