from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type

from direct.showbase import MessengerGlobal

from gameplay.resource import BaseResource

from managers import game
from managers.entity import EntityManager
from system.generators.base import BaseGenerator
from system.generators.resource_allocator import ResourceAllocator
from system.pyload import PyLoad
from system.subsystems.hexgen.enums import MapType, OceanType, HexFeature
from system.generators.base import WorldParams
from system.mesh import HexGrid

if TYPE_CHECKING:
    from main import SCIV
    from system.game_settings import GameSettings
    from system.subsystems.hexgen.grid import Grid
    from gameplay.tiles.base_tile import BaseTile, Hex


class Basic(BaseGenerator):
    NAME = "CivLike"
    DESCRIPTION = "Generates a hex-based map using HexGen."

    def __init__(self, config: "GameSettings", base: "SCIV"):
        super().__init__(config, base=base)
        self.config: "GameSettings" = config
        from random import randrange

        # Random seed
        self.seed = randrange(0, 10**12 - 1)

        # Load tile definitions
        self.tiles_dict: Dict[str, Type[BaseTile]] = self.load_tiles()
        self.grid: Dict[Tuple[int, int], BaseTile] = {}
        self.map: Dict[str, BaseTile] = self.world.map
        self.mesh_grid: Optional[HexGrid] = None

        self.resource_allocator: Optional[ResourceAllocator] = None

        self.world_generation_stats: Dict[str, Any] = {}
        self.number_of_tiles: int = self.config.width * self.config.height

        self.map_params = {
            "map_type": MapType.terran,
            "surface_pressure": 1013.25,
            "size": max(self.config.width, self.config.height),
            "year_length": 365,
            "day_length": 24,
            "base_temp": 0,
            "avg_temp": 10,
            "sea_percent": 40,
            "hydrosphere": True,
            "ocean_type": [OceanType.water],
            "random_seed": self.seed,
            "roughness": 18,
            "height_range": (0, 240),
            "pressure": 1,  # bar
            "axial_tilt": 15,  # This is the most important part of temperature its temperature range in degrees dont go over like 30 for a very hot map 10 for a cold map 18 is earth about
            # features
            "craters": True,
            "volcanoes": True,
            "volcano_area_size": 1,
            "num_volcanoes": max(5, self.number_of_tiles // 1000),
            "num_rivers": self.number_of_tiles // 100,
            # territories
            "num_territories": self.number_of_tiles // 100,
        }

    def load_tiles(self) -> Dict[str, Type["BaseTile"]]:
        """Loads tile classes dynamically."""
        from gameplay.tiles.base_tile import BaseTile

        classes = PyLoad.load_classes("gameplay/tiles", base_classes=BaseTile)
        # Remove the base class from the list
        if "BaseTile" in classes:
            del classes["BaseTile"]
        return classes

    def generate(self) -> bool:
        """Generates the hex map, instantiates tiles without their default models, then builds GPU meshes using the tile's own Z calculation."""
        from system.subsystems.hexgen.mapgen import MapGen

        # Step 1: Generate raw world data via HexGen
        MessengerGlobal.messenger.send("ui.loading.next_step", ["Generating map..."])
        start_time = datetime.now()
        self.hexgen_map = MapGen(self.map_params, debug=True)
        self.hex_grid: Grid = self.hexgen_map.hex_grid
        end_hexgen_time = datetime.now()

        # Step 2: Classify terrain and compute 2D render positions
        MessengerGlobal.messenger.send("ui.loading.next_step", ["Converting map..."])
        start_conversion = datetime.now()
        for col in range(self.config.height):
            for row in range(self.config.width):
                hex_tile = self.hex_grid.grid[col][row]  # type: ignore
                # Stagger odd-q layout
                x = col * self.world.col_spacing
                y = row * self.world.row_spacing + (self.world.row_spacing * 0.5 if col % 2 else 0)
                terrain = self.classify_terrain(hex_tile)
                hex_tile.terrain = terrain
                hex_tile.render_pos = (x, y)
        end_conversion = datetime.now()

        # Step 3: Instantiate tile objects WITHOUT rendering their Panda3D models
        MessengerGlobal.messenger.send("ui.loading.next_step", ["Instantiating tiles..."])
        start_inst = datetime.now()
        self.instantiate_tiles()
        end_inst = datetime.now()

        # Step 4: Build and position GPU meshes based on each tile's calculated Z
        MessengerGlobal.messenger.send("ui.loading.next_step", ["Building meshes..."])
        start_mesh = datetime.now()
        # Create a height map from each tile's pos_z

        hexes = [tile for tile in self.world.grid.values()]

        self.mesh_grid = HexGrid(
            radius=1.0,
            tiles=list(self.world.grid.values()),
            cols=self.config.width,
            rows=self.config.height,
        )
        self.mesh_grid.grid_np.instance_to(self.base.render)  # type: ignore
        game.Game.get_singleton_instance().mesh_grid = self.mesh_grid

        for tile in hexes:
            tile.recalc_grid_position(1)

        end_mesh = datetime.now()

        # Step 5: Allocate resources and place units
        MessengerGlobal.messenger.send("ui.loading.next_step", ["Allocating resources..."])
        start_res = datetime.now()
        self.resource_allocator = ResourceAllocator(self.world.grid, self.get_all_resources())
        self.resource_allocator.allocate_resources()
        end_res = datetime.now()

        MessengerGlobal.messenger.send("ui.loading.next_step", ["Placing starting units..."])
        start_units = datetime.now()
        self.place_starting_units()
        end_units = datetime.now()

        # Record timing stats
        self.world_generation_stats["durations"] = {
            "hexgen": round((end_hexgen_time - start_time).total_seconds() * 1000, 2),
            "conversion": round((end_conversion - start_conversion).total_seconds() * 1000, 2),
            "instantiate_tiles": round((end_inst - start_inst).total_seconds() * 1000, 2),
            "mesh_build": round((end_mesh - start_mesh).total_seconds() * 1000, 2),
            "resources": round((end_res - start_res).total_seconds() * 1000, 2),
            "units": round((end_units - start_units).total_seconds() * 1000, 2),
        }
        self.world_generation_stats.update(
            {
                "seed": self.seed,
                "map_size": (self.config.width, self.config.height),
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
            }
        )
        EntityManager.get_singleton_instance().add_meta_data("world_generation_stats", self.world_generation_stats)

        MessengerGlobal.messenger.send("ui.loading.next_step", ["Done..."])
        return True

    def classify_terrain(self, hex_tile: "Hex") -> str:
        biome_id: int = hex_tile.biome.id  # type: ignore
        geoform_id: int = hex_tile.geoform_type.id  # type: ignore
        hex_temp: int = int(hex_tile.temperature[0])  # type: ignore
        hex_alt: int = int(hex_tile.altitude)  # type: ignore

        if HexFeature.volcano in hex_tile.features:  # if we dont have flow its just the area around it.
            return "Volcano"

        # Water check
        if hex_tile.is_water:
            if geoform_id == 4 or HexFeature.lake in hex_tile.features:
                return "Lake"
            elif geoform_id == 2:
                return "Sea"
            elif hex_tile.is_coast and geoform_id != 2:  # Shallow water, For some reason water is desert or grassland
                return "Coast"
            elif biome_id in (WorldParams.tundra,) or hex_tile.temperature[0] < -1:
                return "SeaIce"
            else:
                return "Sea"
        elif hex_tile.is_land:
            # Its land

            # Check for mountains
            if hex_tile.altitude > WorldParams.hills_to_mountains_threshold:
                if hex_temp < -2:
                    return "MountainSnow"
                else:
                    return "Mountain"
            # Check for hills
            else:
                if int(hex_alt) > WorldParams.flat_to_hills_threshold:
                    if (
                        biome_id
                        in (
                            WorldParams.grasslands,
                            WorldParams.scrubland,
                        )
                        and hex_temp >= WorldParams.forest_lower_threshold
                        and hex_temp <= WorldParams.grass_temperature_upper_threshold
                    ):
                        return "HillsGrassland"
                    elif (
                        biome_id
                        in (
                            WorldParams.boreal_forest,
                            WorldParams.temperate_forest,
                            WorldParams.temperate_rainforest,
                            WorldParams.tropical_forest,
                            WorldParams.tropical_rainforest,
                        )
                        and hex_temp >= WorldParams.forest_lower_threshold
                    ):
                        return "HillsForest"
                    elif biome_id in (WorldParams.savanna, WorldParams.desert, WorldParams.scrubland):
                        return "HillsDesert"
                    elif (
                        biome_id in (WorldParams.alpine_tundra, WorldParams.arctic, WorldParams.boreal_forest)
                        and hex_temp < 0
                    ):
                        return "HillsSnow"
                    elif hex_temp < WorldParams.grass_temperature_lower_threshold and biome_id not in (
                        WorldParams.scrubland,
                        WorldParams.savanna,
                        WorldParams.desert,
                    ):
                        return "HillsTundra"
                else:
                    if (
                        biome_id in (WorldParams.desert,) and hex_temp > WorldParams.desert_temperature_threshold
                    ):  # Desert or savannah, keep this high as it needs to be checked first before grassland
                        return "FlatDesert"
                    elif (
                        biome_id in (WorldParams.grasslands, WorldParams.tropical_forest)
                        and hex_tile.moisture > WorldParams.moisture_threshold_mangrove_jungle
                    ):  # Virtual Mangrove Actual grassland with high moister
                        return "FlatJungle"
                    elif (
                        biome_id in (WorldParams.tropical_forest,)
                        and hex_temp < WorldParams.light_jungle_temperature_threshold
                    ):
                        return "FlatLightJungle"
                    elif biome_id in (WorldParams.scrubland,) or (
                        biome_id == WorldParams.grasslands and hex_temp < WorldParams.schrubland_temperature_threshold
                    ):  # Virtual Mangrove Actual scrubland with low moister
                        return "FlatScrubland"
                    elif (
                        biome_id in (WorldParams.savanna, WorldParams.desert)
                        and hex_temp <= WorldParams.desert_temperature_threshold
                    ) or biome_id in (
                        WorldParams.grasslands,
                    ):  # Grassland and when its a "desert" but to cold to be a desert
                        return "FlatGrass"
                    elif biome_id in (WorldParams.savanna,):  # Savanna
                        return "FlatSavanna"
                    elif biome_id in (
                        WorldParams.boreal_forest,
                        WorldParams.tropical_rainforest,
                    ):  # flat heavy forrest virtual (cold boreal forest)
                        if hex_temp < WorldParams.cold_forrest_temperature_threshold:
                            return "FlatPineForest"
                        return "FlatHeavyForest"
                    elif biome_id in (
                        WorldParams.tropical_rainforest,
                    ):  # Fake tile type: Jungle not (Tropical Rainforest)
                        pass
                        # return "FlatJungle"
                    elif biome_id in (
                        WorldParams.tropical_forest,
                        WorldParams.temperate_rainforest,
                        WorldParams.temperate_forest,
                        WorldParams.boreal_forest,
                    ):  # forest
                        return "FlatForrest"

                    elif biome_id in (WorldParams.scrubland,):  # Scrubland
                        return "FlatScrubland"
                    elif biome_id in (WorldParams.arctic,):  # Arctic / Ice
                        return "FlatIce"
                    elif biome_id in (WorldParams.tundra, WorldParams.alpine_tundra):  # 2 Tundra, 3 Alpine Tundra
                        if hex_temp < -0:  # This is a cold tile or alpine
                            return "FlatTundraSnow"
                        else:
                            return "FlatTundra"  # This is a normal tundra should be just 2 left as 3 is handled above
                    elif biome_id in (13,):  # Wasteland
                        return "FlatWasteland"
                    elif biome_id in (WorldParams.tundra,):
                        return "FlatTundra"

        raise ValueError(
            f"Terrain not found for hex_tile: {hex_tile}|{hex_tile.biome}[{biome_id}]|{hex_tile.geoform_type}|{int(hex_tile.temperature[0])}|{hex_tile.altitude}"
        )

    def instantiate_tiles(self):
        """Creates Tile objects and places them on the grid."""
        for col in range(self.config.height):
            for row in range(self.config.width):
                hex_tile = self.hex_grid.grid[col][row]  # type: ignore

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
                _, _, obj_instance.pos_z = obj_instance.calculate_z_pos_on_altitude()
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

    def _hex_distance(self, hex1: "Hex", hex2: "Hex") -> int:
        """
        Calculates the distance between two hex tiles using axial coordinates.
        """
        dx = abs(hex1.x - hex2.x)
        dy = abs(hex1.y - hex2.y)
        return max(dx, dy, abs(dx - dy))
