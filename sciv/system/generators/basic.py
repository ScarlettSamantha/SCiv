import weakref
from datetime import datetime
from random import randrange
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple, Type
from zlib import crc32

from direct.showbase import MessengerGlobal
from gameplay.repositories.tile import TileRepository
from gameplay.resource import BaseResource
from helpers.tiles import Tiles
from managers import game
from managers.entity import EntityManager
from system.generators.base import BaseGenerator, WorldParams
from system.generators.resource_allocator import ResourceAllocator
from system.pyload import PyLoad
from system.subsystems.hexgen.enums import GeoformType, HexFeature, MapType, OceanType
from system.tile_grid import TileModelGrid

if TYPE_CHECKING:
    from game import OpenCiv
    from gameplay.tile import Tile
    from system.game_settings import GameSettings
    from system.subsystems.hexgen.grid import Grid
    from system.subsystems.hexgen.hex import Hex


class Basic(BaseGenerator):
    NAME = "CivLike"
    DESCRIPTION = "Generates a hex-based map using HexGen."

    def __init__(self, config: "GameSettings", base: "OpenCiv"):
        super().__init__(config, base=base)
        self.config: "GameSettings" = config

        self.seed: Optional[int] = config.seed if config.seed is not None else None
        self.generate_seed = self.seed is None

        self.tiles_dict: Dict[str, Type[Tile]] = self.load_tiles()
        self.map: Dict[str, Tile] = self.world.map

        self.model_grid: Optional[TileModelGrid] = None

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
            "avg_temp": 10,  # 8 is cold 10 is average, 14 is decent, 18 is hot, 22 is very hot
            "sea_percent": 55,
            "hydrosphere": True,
            "ocean_type": [OceanType.water],
            "random_seed": self.seed,
            "roughness": 17,  # <10 huge patches; 18 nice; >24 too rough
            "height_range": (0, 240),
            "pressure": 1,  # bar
            "axial_tilt": 18,
            "craters": True,
            "volcanoes": True,
            "volcano_area_size": 1,
            "num_volcanoes": max(1, self.number_of_tiles // 2000),
            "num_rivers": self.number_of_tiles // 400,
            "num_territories": self.number_of_tiles // 300,
            "lake_to_sea_tiles": 100,
            "sea_to_ocean_tiles": 150,
        }

    def randomize_seed(self) -> int:
        time = str(crc32(str(int(datetime.now().timestamp() * 1000)).encode()))[:-3]
        rand = str(randrange(2**12, 2**30))[:-3]
        micro = str(datetime.now().microsecond)[:-3]

        self.seed = int(f"{time}{rand}{micro}")
        self.map_params["random_seed"] = self.seed
        self.config.seed = self.seed
        return self.seed

    def load_tiles(self) -> Dict[str, Type["Tile"]]:
        from gameplay.tile import Tile

        classes = PyLoad.load_classes("gameplay/tiles", base_classes=Tile)
        if "Tile" in classes:
            del classes["Tile"]
        return classes

    def generate(self) -> bool:
        from system.subsystems.hexgen.mapgen import MapGen

        MessengerGlobal.messenger.send("ui.loading.next_step", ["Generating map..."])
        start_time = datetime.now()
        self.hexgen_map = MapGen(self.map_params, debug=True)
        self.hex_grid: Grid = self.hexgen_map.hex_grid
        end_hexgen_time = datetime.now()

        MessengerGlobal.messenger.send("ui.loading.next_step", ["Converting map..."])
        start_conversion = datetime.now()
        for col in range(self.config.height):
            for row in range(self.config.width):
                hex_tile: "Hex" = self.hex_grid.grid[col][row]  # type: ignore
                x = col * self.world.col_spacing
                y = row * self.world.row_spacing + (self.world.row_spacing * 0.5 if col % 2 else 0)
                terrain = self.classify_terrain(hex_tile)
                hex_tile.terrain = terrain
                hex_tile.render_pos = (x, y)
        end_conversion = datetime.now()

        start_water_level_adjustment: datetime = datetime.now()
        self.adjust_water_levels()
        end_water_level_adjustment: datetime = datetime.now()

        self._desertize_adjacent_tundra()

        MessengerGlobal.messenger.send("ui.loading.next_step", ["Instantiating tiles..."])
        start_inst = datetime.now()
        self.instantiate_tiles()
        end_inst = datetime.now()

        self._assign_tile_models()

        MessengerGlobal.messenger.send("ui.loading.next_step", ["Placing terrain models..."])
        start_models = datetime.now()

        hexes: List[Tile] = list(self.world.grid.values())

        self.model_grid = TileModelGrid(
            tiles=hexes,
            radius=1.0,
            cols=self.config.width,
            rows=self.config.height,
            default_model_path="assets/models/terrain/flat_grassland.glb",
        )

        self.model_grid.attach_to_render()
        self.model_grid.collect()

        g = game.Game.get_singleton_instance()
        g.model_grid = self.model_grid  # type: ignore[attr-defined]
        g.tile_hex_grid = self.model_grid  # type: ignore[attr-defined]

        for tile in hexes:
            tile.recalculate_grid_position(1)

        TileRepository.grid = self.world.grid

        end_models = datetime.now()

        MessengerGlobal.messenger.send("ui.loading.next_step", ["Allocating resources..."])
        start_res = datetime.now()
        self.resource_allocator = ResourceAllocator(self.world.grid, self.get_all_resources())
        self.resource_allocator.allocate_resources()
        end_res = datetime.now()

        MessengerGlobal.messenger.send("ui.loading.next_step", ["Placing starting units..."])
        start_units = datetime.now()
        self.place_starting_units()
        end_units = datetime.now()

        self.world_generation_stats["durations"] = {
            "hexgen": round((end_hexgen_time - start_time).total_seconds() * 1000, 2),
            "conversion": round((end_conversion - start_conversion).total_seconds() * 1000, 2),
            "water_level_adjustment": round(
                (end_water_level_adjustment - start_water_level_adjustment).total_seconds() * 1000, 2
            ),
            "instantiate_tiles": round((end_inst - start_inst).total_seconds() * 1000, 2),
            "mesh_build": round((end_models - start_models).total_seconds() * 1000, 2),  # kept key for continuity
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
        self.grid = self.world.grid
        return True

    def classify_terrain(self, hex_tile: "Hex") -> str:
        biome_id: int = int(
            getattr(hex_tile, "biome_id", getattr(getattr(hex_tile, "biome", None), "id", WorldParams.grasslands))
        )

        hex_temp = float(hex_tile.temperature[0])
        hex_temp_i = int(round(hex_temp))
        moisture_like = float(hex_tile.moisture)

        geotype = getattr(hex_tile, "geoform_type", None)
        hex_alt: int = int(hex_tile.altitude)

        if HexFeature.volcano in hex_tile.features:
            return "Volcano"

        if hex_tile.is_water:
            if geotype == GeoformType.lake:
                return "Lake"
            if hex_tile.is_coast:
                return "Coast"
            if geotype in (GeoformType.sea, GeoformType.ocean) and hex_tile.temperature[0] < -1:
                return "SeaIce"
            return "Sea"

        if hex_tile.altitude > WorldParams.hills_to_mountains_threshold:
            return "MountainSnow" if hex_temp_i < -2 else "Mountain"

        if hex_alt > WorldParams.flat_to_hills_threshold:
            if biome_id not in (WorldParams.scrubland, WorldParams.savanna, WorldParams.desert) and hex_temp_i < 0:
                return "HillsSnow"
            elif biome_id in (WorldParams.savanna, WorldParams.desert):
                return "HillsDesert"
            elif (
                biome_id in (WorldParams.grasslands, WorldParams.scrubland)
                and WorldParams.forest_lower_threshold <= hex_temp <= WorldParams.grass_temperature_upper_threshold
                and moisture_like < WorldParams.forest_lower_threshold
            ):
                return "HillsGrassland"
            elif (
                biome_id
                in (
                    WorldParams.grasslands,
                    WorldParams.tropical_forest,
                    WorldParams.temperate_rainforest,
                    WorldParams.temperate_forest,
                    WorldParams.boreal_forest,
                    WorldParams.scrubland,
                )
                and moisture_like >= WorldParams.forest_lower_threshold
            ):
                return "HillsForest"
            elif hex_temp < WorldParams.forest_lower_threshold and biome_id not in (
                WorldParams.scrubland,
                WorldParams.savanna,
                WorldParams.desert,
            ):
                return "HillsTundra"

        if biome_id == WorldParams.tropical_forest:
            return "FlatLightJungle"

        if biome_id == WorldParams.temperate_rainforest:
            return "FlatJungle"

        if biome_id == WorldParams.grasslands:
            return "FlatGrass"

        if biome_id == WorldParams.desert:
            return "FlatDesert"

        if biome_id == WorldParams.temperate_forest:
            if moisture_like < WorldParams.moisture_threshold_heavy_forest:
                return "FlatForest"
            else:
                return "FlatHeavyForest"

        if biome_id == WorldParams.boreal_forest:
            return "FlatPineForest"

        if biome_id == WorldParams.tropical_rainforest:
            return "FlatForest"

        if biome_id == WorldParams.savanna:
            return "FlatSavanna"

        if biome_id == WorldParams.scrubland:
            return "FlatScrubland"

        if biome_id == WorldParams.arctic:
            return "FlatIce"

        if biome_id == WorldParams.alpine_tundra:
            return "FlatTundraSnow"

        if biome_id == WorldParams.tundra:
            return "FlatTundra"

        raise ValueError(f"Could not classify terrain for hex {hex_tile} with biome id {biome_id}")

    def _desertize_adjacent_tundra(self) -> int:
        height = self.config.height
        width = self.config.width
        raw = self.hex_grid.grid

        DESERTS = {"FlatDesert", "HillsDesert"}
        TUNDRA_FLATS = {"FlatTundra"}

        def neighbors(c: int, r: int):
            for dc, dr in Tiles.get_directions_per_col(c):
                nc, nr = c + dc, r + dr
                if 0 <= nc < height and 0 <= nr < width:
                    yield nc, nr

        def terrain_at(c: int, r: int) -> str:
            h = raw[c][r]
            t = h.terrain
            if not t:
                tile = self.world.grid.get((c, r))
                if tile is not None:
                    t = tile.get_terrain().get_key()
            return t or ""

        to_convert: List[Tuple[int, int]] = []
        for c in range(height):
            for r in range(width):
                terr = terrain_at(c, r)
                if terr not in TUNDRA_FLATS:
                    continue
                for nc, nr in neighbors(c, r):
                    if terrain_at(nc, nr) in DESERTS:
                        to_convert.append((c, r))
                        break

        for c, r in to_convert:
            self.hex_grid.grid[c][r].terrain = "FlatDesert"

        return len(to_convert)

    def instantiate_tiles(self):
        for col in range(self.config.height):
            for row in range(self.config.width):
                hex_tile = self.hex_grid.grid[col][row]  # type: ignore

                x, y = hex_tile.x, hex_tile.y
                terrain = hex_tile.terrain
                tile_class = self.tiles_dict.get(terrain, self.tiles_dict.get("FlatGrassland"))
                if tile_class is None:
                    raise ValueError(f"Tile class for terrain '{terrain}' not found.")

                render_x = col * self.world.col_spacing
                if col % 2 == 1:
                    render_y = row * self.world.row_spacing + (self.world.row_spacing * 0.5)
                else:
                    render_y = row * self.world.row_spacing

                obj_instance: Tile = tile_class(x, y, render_x, render_y)
                self.enrich_from_extra_data(hex=hex_tile, tile=obj_instance)
                obj_instance.pos_z = obj_instance.calculate_z_pos_on_altitude()[2]
                self.map[obj_instance.tag] = obj_instance
                self.world.grid[(col, row)] = obj_instance

    @classmethod
    def enrich_from_extra_data(cls, hex: "Hex", tile: "Tile") -> "Tile":
        from gameplay.tile import Tile

        def _waterbody_touches_edge() -> bool:
            g = getattr(hex, "geoform", None)
            if not g:
                return False
            max_i = hex.grid.size - 1  # grid is square
            for h in g.hexes:
                if h.x == 0 or h.y == 0 or h.x == max_i or h.y == max_i:
                    return True
            return False

        tile.altitude = float(hex.altitude)
        tile.temperature = round(hex.base_temperature[0], 2)
        tile.moisture = float(hex.moisture)
        tile._biome = hex.biome.list()[0]  # set by classify_terrain  # type: ignore
        if hex.geoform_type is not None:
            tile.geoforms = hex.geoform_type
        tile.features = set(hex.features)

        gtype = getattr(hex, "geoform_type", None)
        tile.is_water = bool(hex.is_water)
        tile.is_land = bool(hex.is_land)

        tile.is_lake = bool(gtype == GeoformType.lake)
        tile.is_sea = bool(gtype in (GeoformType.sea, GeoformType.ocean))
        tile.is_inland_sea = bool(gtype == GeoformType.sea and not _waterbody_touches_edge())

        # Coast: water-side coastline only (and never true for lakes)
        tile.is_coast = bool(hex.is_coast)

        tile.terrain = str(hex.terrain)  # type: ignore

        # Hemisphere
        tile.hemisphere = Tile.HEMISPHERE_NORTH if hex.hemisphere.value == "Northern" else Tile.HEMISPHERE_SOUTH

        # Optional enum text label for UI
        if hex.geoform_type is not None:
            tile.geoforms = hex.geoform_type.list()[0]

        # Resource instance
        if (resource := hex.get_gameplay_resource()) is not None:
            tile.instance_resource(resource)

        # Edges (keep as-is)
        edge_names: List[str] = list(tile.edges.keys())
        if len(edge_names) != 6:
            raise ValueError(f"Hex {hex} has {len(edge_names)} edges, expected 6.")

        for i, edge_name in enumerate(tile.edges.keys()):
            if hex.edges[i] is not None:
                tile.edges[edge_name] = weakref.ref(hex.edges[i])  # type: ignore
            else:
                tile.edges[edge_name] = None

        return tile

    def adjust_water_levels(self) -> None:
        height = self.config.height
        width = self.config.width

        visited: Set[Tuple[int, int]] = set()

        raw = self.hex_grid.grid  # raw[col][row] => Hex

        def neighbors(c: int, r: int) -> List[Tuple[int, int]]:
            offsets = Tiles.get_directions_per_col(c)
            result: List[Tuple[int, int]] = []
            for dc, dr in offsets:
                nc, nr = c + dc, r + dr
                if 0 <= nc < height and 0 <= nr < width:
                    result.append((nc, nr))
            return result

        for col in range(height):
            for row in range(width):
                hex_tile = raw[col][row]
                if not hex_tile.is_water or (col, row) in visited:
                    continue

                queue = [(col, row)]
                visited.add((col, row))
                water_cluster = [(col, row)]
                idx = 0
                while idx < len(queue):
                    c0, r0 = queue[idx]
                    idx += 1
                    for nc, nr in neighbors(c0, r0):
                        neighbor_hex = raw[nc][nr]
                        if neighbor_hex.is_water and (nc, nr) not in visited:
                            visited.add((nc, nr))
                            queue.append((nc, nr))
                            water_cluster.append((nc, nr))

                border_altitudes: List[float] = []
                for wc, wr in water_cluster:
                    for nc, nr in neighbors(wc, wr):
                        neighbor_hex = raw[nc][nr]
                        if neighbor_hex.is_land:
                            border_altitudes.append(neighbor_hex.altitude)

                if not border_altitudes:
                    continue

                min_adj_land = min(border_altitudes)
                water_level = min_adj_land - 1

                for wc, wr in water_cluster:
                    raw[wc][wr].altitude = water_level

    def get_all_resources(self) -> List[Type[BaseResource]]:
        from gameplay.repositories.resources import ResourceRepository
        from gameplay.resource import ResourceType

        instance = ResourceRepository()
        resources: List[Type[BaseResource]] = instance.all_by_type(
            [ResourceType.STRATEGIC, ResourceType.BONUS, ResourceType.LUXURY]
        )
        return resources

    def _hex_distance(self, hex1: "Hex", hex2: "Hex") -> int:
        dx = abs(hex1.x - hex2.x)
        dy = abs(hex1.y - hex2.y)
        return max(dx, dy, abs(dx - dy))

    def _assign_tile_models(self) -> None:
        for _, tile in self.world.grid.items():
            model_key = tile.get_terrain().get_key()

            path: str = tile.get_model()
            scale = getattr(tile, "model_scale", 1.0)
            scale = (float(scale), float(scale), float(scale))
            hpr = getattr(tile, "model_hpr", (0.0, 0.0, 0.0))
            z_off = float(getattr(tile, "model_z_offset", 0.0))

            setattr(tile, "model_key", str(model_key))
            setattr(tile, "model_path", str(path))
            setattr(tile, "model_scale", tuple(map(float, scale)))
            setattr(tile, "model_hpr", tuple(map(float, hpr)))
            setattr(tile, "model_z_offset", float(z_off))
