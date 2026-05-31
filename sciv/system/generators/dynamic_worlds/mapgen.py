import sys
from typing import Any

try:
    from helpers.debug import Debug as DebugHelper
except Exception:
    class _FallbackDebugHelper:
        @staticmethod
        def world_generation(override: bool | None = None) -> bool:
            return bool(override) if override is not None else False

    DebugHelper = _FallbackDebugHelper

from system.generators.dynamic_worlds.biomes import apply_biome_style_profile
from system.generators.dynamic_worlds.landmasses import apply_landmass_heightmap_profile
from system.generators.dynamic_worlds.rivers import apply_dynamic_river_profile
from system.subsystems.hexgen.geoform import Geoform
from system.subsystems.hexgen.grid import Grid
from system.subsystems.hexgen.heightmap import Heightmap
from system.subsystems.hexgen.hex import Hex
from system.subsystems.hexgen.mapgen import MapGen, Timer, default_params
from system.subsystems.hexgen.river import RiverSegment
from system.subsystems.hexgen.territory import Territory

sys.setrecursionlimit(10000000)


class DynamicMapGen(MapGen):
    def __init__(
        self,
        params: dict[str, Any],
        *,
        map_script: str,
        biome_style: str,
        debug: bool = False,
    ):
        self.params: dict[str, Any] = {**default_params, **params}
        self.map_script = map_script
        self.biome_style = biome_style
        self.debug = bool(debug) or DebugHelper.world_generation()

        self._seed_rngs()

        with Timer("Building Dynamic Heightmap", self.debug):
            self.heightmap = Heightmap(self.params, self.debug)
            self.landmass_shape_stats = apply_landmass_heightmap_profile(
                self.heightmap,
                map_script=self.map_script,
                rng=self.rng,
            )

        self.hex_grid: Grid = Grid(self.heightmap, self.params)
        self.ocean_connection_stats: dict[str, int] = {
            "initial_edge_oceans": 0,
            "channels_carved": 0,
            "tiles_carved": 0,
            "final_edge_oceans": 0,
        }
        if bool(self.params.get("force_connected_oceans", False)):
            with Timer("Connecting main oceans", self.debug):
                self.ocean_connection_stats = self._connect_main_oceans()
        if self.debug:
            print("\tAverage Height: {}".format(self.hex_grid.average_height))
            print("\tHighest Height: {}".format(self.hex_grid.highest_height))
            print("\tLowest Height: {}".format(self.hex_grid.lowest_height))

        self.num_tiles: int = self.hex_grid.size * self.hex_grid.size

        self.rivers: list[Any] = []
        self.rivers_sources: list[RiverSegment] = []

        with Timer("Computing hex distances", self.debug):
            self._get_distances()

        self.river_shape_stats: dict[str, int] = {
            "tributaries_added": 0,
            "connectors_added": 0,
            "distributaries_added": 0,
            "valley_segments": 0,
        }
        if self.params.get("hydrosphere"):
            self._generate_rivers()
            self.river_shape_stats = apply_dynamic_river_profile(
                self,
                map_script=self.map_script,
                biome_style=self.biome_style,
            )

        factor_min_max = 2
        max_aquifers = self.num_tiles // 80
        min_aquifers = max_aquifers // factor_min_max
        num_aquifers = self.rng.randint(min_aquifers, max_aquifers) if max_aquifers > 0 else 0

        if not self.params.get("hydrosphere") or int(self.params.get("sea_percent", 0)) == 100:
            num_aquifers = 0

        aquifers: list[Hex] = []
        while len(aquifers) < num_aquifers:
            rx = self.rng.randint(0, len(self.hex_grid.grid) - 1)
            ry = self.rng.randint(0, len(self.hex_grid.grid) - 1)
            current_hex: Hex = self.hex_grid.grid[rx][ry]
            if current_hex.is_land and current_hex.moisture < 5:
                aquifers.append(current_hex)

        for aquifer_hex in aquifers:
            for bubble_hex in aquifer_hex.bubble(distance=3):
                if bubble_hex.is_land:
                    bubble_hex.moisture += self.rng.randint(0, 2)
            for bubble_hex in aquifer_hex.bubble(distance=2):
                if bubble_hex.is_land:
                    bubble_hex.moisture += 1
            for bubble_hex in aquifer_hex.surrounding:
                if bubble_hex.is_land:
                    bubble_hex.moisture += 1

        if self.params.get("craters") is True:
            self.generate_craters()

        if self.params.get("volcanoes", True):
            self.generate_volcanoes()

        self.territories: list[Territory] = []
        self.geoforms: list[Geoform] = []

        self.generate_territories()
        self._determine_landforms()
        self._detect_lakes()

        if self.params.get("hydrosphere"):
            with Timer("Applying moisture diffusion (coast/rivers/lakes)", self.debug):
                self._apply_moisture()

        self.biome_shape_stats = apply_biome_style_profile(
            self.hex_grid,
            biome_style=self.biome_style,
            seed=self.params.get("random_seed"),
        )

        self._integrity_checks()
