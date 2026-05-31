from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from gameplay.founding.site_scoring import TileScoringProfile, score_tile
from gameplay.repositories.tile import TileRepository
from managers.entity import EntityManager
from system.generators.base import GeneratorSetupField
from system.generators.basic import Basic
from system.generators.dynamic_worlds import (
    apply_biome_region_names,
    apply_landmass_names,
    apply_river_names,
    biome_style_choices,
    build_dynamic_map_params,
    build_named_biome_regions,
    build_named_landmasses,
    build_named_rivers,
    get_biome_style_profile_name,
    get_dynamic_tile_scoring_profile,
    get_landmass_profile_name,
    landmass_choices,
    ocean_connectivity_choices,
    river_amount_choices,
    river_length_choices,
    river_network_choices,
    tributary_choices,
)
from system.generators.dynamic_worlds.coastline import apply_scripted_coastline_polish

if TYPE_CHECKING:
    from gameplay.tile import Tile


class Dynamic(Basic):
    NAME = "Dynamic Worlds"
    DESCRIPTION = "Preset-driven generator with configurable landmass and climate variety."

    SETUP_FIELDS: tuple[GeneratorSetupField, ...] = (
        GeneratorSetupField(
            key="map_script",
            label="Landmass",
            default="continents",
            choices=landmass_choices(),
            description="Controls the broad landmass style used by the Dynamic Worlds presets.",
        ),
        GeneratorSetupField(
            key="biome_style",
            label="Biome Style",
            default="balanced",
            choices=biome_style_choices(),
            description="Applies a named biome bias on top of the temperature and humidity settings.",
        ),
        GeneratorSetupField(
            key="world_age",
            label="World Age",
            default="standard",
            choices=(("Young", "young"), ("Standard", "standard"), ("Old", "old")),
            description="Younger worlds are rougher and more volcanic; older worlds are gentler.",
        ),
        GeneratorSetupField(
            key="temperature",
            label="Temperature",
            default="temperate",
            choices=(("Cool", "cool"), ("Temperate", "temperate"), ("Hot", "hot")),
            description="Adjusts global temperature bands and the likely biome mix.",
        ),
        GeneratorSetupField(
            key="humidity",
            label="Humidity",
            default="normal",
            choices=(("Arid", "arid"), ("Normal", "normal"), ("Wet", "wet")),
            description="Biases desert coverage, moisture diffusion, and river frequency.",
        ),
        GeneratorSetupField(
            key="sea_level",
            label="Sea Level",
            default="normal",
            choices=(("Low", "low"), ("Normal", "normal"), ("High", "high")),
            description="Biases the total water coverage used by the world generator.",
        ),
        GeneratorSetupField(
            key="ocean_connectivity",
            label="Ocean Connectivity",
            default="natural",
            choices=ocean_connectivity_choices(),
            description="Can force all edge-touching ocean basins to connect through carved straits.",
        ),
        GeneratorSetupField(
            key="river_amount",
            label="River Amount",
            default="normal",
            choices=river_amount_choices(),
            description="Controls how many main rivers Dynamic Worlds tries to generate.",
        ),
        GeneratorSetupField(
            key="river_length",
            label="River Length",
            default="normal",
            choices=river_length_choices(),
            description="Biases river sources farther inland for shorter or longer river chains.",
        ),
        GeneratorSetupField(
            key="tributaries",
            label="Tributaries",
            default="normal",
            choices=tributary_choices(),
            description="Controls how aggressively Dynamic Worlds grows extra tributary branches.",
        ),
        GeneratorSetupField(
            key="river_network",
            label="River Networks",
            default="natural",
            choices=river_network_choices(),
            description="Controls split-and-rejoin side channels plus cross-basin river connectors.",
        ),
    )

    @classmethod
    def get_setup_fields(cls) -> tuple[GeneratorSetupField, ...]:
        return cls.SETUP_FIELDS

    def build_map_params(self) -> Dict[str, Any]:
        map_script = str(self.setup_options.get("map_script", "continents"))
        biome_style = str(self.setup_options.get("biome_style", "balanced"))
        world_age = str(self.setup_options.get("world_age", "standard"))
        temperature = str(self.setup_options.get("temperature", "temperate"))
        humidity = str(self.setup_options.get("humidity", "normal"))
        sea_level = str(self.setup_options.get("sea_level", "normal"))
        ocean_connectivity = str(self.setup_options.get("ocean_connectivity", "natural"))
        river_amount = str(self.setup_options.get("river_amount", "normal"))
        river_length = str(self.setup_options.get("river_length", "normal"))
        tributaries = str(self.setup_options.get("tributaries", "normal"))
        river_network = str(self.setup_options.get("river_network", "natural"))
        return build_dynamic_map_params(
            super().build_map_params(),
            map_script=map_script,
            biome_style=biome_style,
            world_age=world_age,
            temperature=temperature,
            humidity=humidity,
            sea_level=sea_level,
            ocean_connectivity=ocean_connectivity,
            river_amount=river_amount,
            river_length=river_length,
            tributaries=tributaries,
            river_network=river_network,
        )

    def generate(self) -> bool:
        from datetime import datetime

        from direct.showbase import MessengerGlobal
        from gameplay.repositories.tile import TileRepository
        from managers import game
        from system.generators.dynamic_worlds.mapgen import DynamicMapGen
        from system.generators.resource_allocator import ResourceAllocator
        from system.tile_grid import TileModelGrid

        map_script = str(self.setup_options.get("map_script", "continents"))
        biome_style = str(self.setup_options.get("biome_style", "balanced"))

        MessengerGlobal.messenger.send("ui.loading.next_step", ["Generating dynamic world..."])
        start_time = datetime.now()
        self.hexgen_map = DynamicMapGen(
            self.map_params,
            map_script=map_script,
            biome_style=biome_style,
            debug=False,
        )
        self.hex_grid = self.hexgen_map.hex_grid
        end_hexgen_time = datetime.now()

        MessengerGlobal.messenger.send("ui.loading.next_step", ["Converting dynamic world..."])
        start_conversion = datetime.now()
        self.prepare_hexes_for_tile_instantiation()
        end_conversion = datetime.now()

        start_water_level_adjustment = datetime.now()
        self.finalize_hexes_for_tile_instantiation()
        end_water_level_adjustment = datetime.now()

        MessengerGlobal.messenger.send("ui.loading.next_step", ["Instantiating tiles..."])
        start_instantiation = datetime.now()
        self.instantiate_tiles()
        end_instantiation = datetime.now()

        self._assign_tile_models()

        MessengerGlobal.messenger.send("ui.loading.next_step", ["Placing terrain models..."])
        start_models = datetime.now()

        hexes = list(self.world.grid.values())

        self.model_grid = TileModelGrid(
            tiles=hexes,
            radius=1.0,
            default_model_path="assets/models/terrain/flat_grassland.glb",
        )

        self.model_grid.attach_to_render()
        self.model_grid.collect()

        active_game = game.Game.get_singleton_instance()
        active_game.model_grid = self.model_grid  # type: ignore[attr-defined]
        active_game.tile_hex_grid = self.model_grid  # type: ignore[attr-defined]

        for tile in hexes:
            tile.recalculate_grid_position(1)

        TileRepository.grid = self.world.grid
        end_models = datetime.now()

        MessengerGlobal.messenger.send("ui.loading.next_step", ["Allocating resources..."])
        start_resources = datetime.now()
        self.resource_allocator = ResourceAllocator(self.world.grid, self.get_all_resources())
        self.resource_allocator.allocate_resources()
        end_resources = datetime.now()

        MessengerGlobal.messenger.send("ui.loading.next_step", ["Placing starting units..."])
        start_units = datetime.now()
        self.place_starting_units()
        end_units = datetime.now()

        self._apply_dynamic_world_metadata()

        self.world_generation_stats["durations"] = {
            "hexgen": round((end_hexgen_time - start_time).total_seconds() * 1000, 2),
            "conversion": round((end_conversion - start_conversion).total_seconds() * 1000, 2),
            "water_level_adjustment": round(
                (end_water_level_adjustment - start_water_level_adjustment).total_seconds() * 1000, 2
            ),
            "instantiate_tiles": round((end_instantiation - start_instantiation).total_seconds() * 1000, 2),
            "mesh_build": round((end_models - start_models).total_seconds() * 1000, 2),
            "resources": round((end_resources - start_resources).total_seconds() * 1000, 2),
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

    def _promote_single_sea_between_coasts(self) -> int:
        promoted = super()._promote_single_sea_between_coasts()
        promoted += apply_scripted_coastline_polish(
            self.hex_grid,
            str(self.setup_options.get("map_script", "continents")),
        )
        return promoted

    def _apply_dynamic_world_metadata(self) -> None:
        visible_coords = set(self.world.grid.keys())
        map_script = str(self.setup_options.get("map_script", "continents"))
        biome_style = str(self.setup_options.get("biome_style", "balanced"))

        landmasses = build_named_landmasses(
            self.hexgen_map.geoforms,
            seed=self.seed,
            visible_coords=visible_coords,
        )
        biome_regions = build_named_biome_regions(
            self.hex_grid,
            seed=self.seed,
            visible_coords=visible_coords,
        )
        rivers = build_named_rivers(
            self.hexgen_map.rivers_sources,
            seed=self.seed,
            visible_coords=visible_coords,
        )

        apply_landmass_names(self.world.grid, landmasses)
        apply_biome_region_names(self.world.grid, biome_regions)
        apply_river_names(self.world.grid, rivers)

        self.world_generation_stats["generator_profiles"] = {
            "landmass": get_landmass_profile_name(map_script),
            "biome_style": get_biome_style_profile_name(biome_style),
        }
        self.world_generation_stats["named_region_counts"] = {
            "landmasses": len(landmasses),
            "biome_regions": len(biome_regions),
            "rivers": len(rivers),
        }
        self.world_generation_stats["dynamic_generation"] = {
            "landmass_shaping": getattr(self.hexgen_map, "landmass_shape_stats", {}),
            "river_shaping": getattr(self.hexgen_map, "river_shape_stats", {}),
            "biome_shaping": getattr(self.hexgen_map, "biome_shape_stats", {}),
        }
        self.world_generation_stats["landmasses"] = [landmass.to_dict() for landmass in landmasses[:24]]
        self.world_generation_stats["biome_regions"] = [region.to_dict() for region in biome_regions[:40]]
        self.world_generation_stats["rivers"] = [river.to_dict() for river in rivers[:40]]

    def place_starting_units(
        self,
        max_attempts: int = 80,
        land_ratio_threshold: float = 0.62,
        land_check_radius: int = 4,
        map_edge_buffer: int = 4,
    ) -> bool:
        from gameplay.units.core.classes.civilian.settler import Settler
        from gameplay.units.core.classes.military.club_man import ClubMan
        from managers.player import PlayerManager

        units_created = 0
        occupied_tiles: List[Tile] = []
        min_distances: List[int] = [8, 7, 6, 5, 4]
        scoring_profile = self._get_scoring_profile()

        def candidate_tiles() -> List[Tile]:
            return [
                tile
                for tile in self.world.grid.values()
                if tile.is_spawnable_upon() and tile.is_passable() and not tile.is_occupied()
            ]

        available_tiles: List[Tile] = candidate_tiles()

        for player in PlayerManager.players().values():
            if player.is_nature or player.is_barbarian:
                continue

            spawn_tile: Optional[Tile] = None
            best_fallback: Optional[Tile] = None
            best_fallback_score: float = float("-inf")

            for min_distance in min_distances:
                available_tiles = candidate_tiles()

                ranked = self._rank_start_tiles(
                    candidates=available_tiles,
                    occupied_tiles=occupied_tiles,
                    scoring_profile=scoring_profile,
                    min_distance=min_distance,
                    max_attempts=max_attempts,
                    land_ratio_threshold=land_ratio_threshold,
                    land_check_radius=land_check_radius,
                    map_edge_buffer=map_edge_buffer,
                )

                if ranked:
                    spawn_tile = ranked[0][0]
                    break

                relaxed_ranked = self._rank_start_tiles(
                    candidates=available_tiles,
                    occupied_tiles=occupied_tiles,
                    scoring_profile=scoring_profile,
                    min_distance=min_distance,
                    max_attempts=max_attempts,
                    land_ratio_threshold=max(0.45, land_ratio_threshold - 0.1),
                    land_check_radius=max(2, land_check_radius - 1),
                    map_edge_buffer=max(2, map_edge_buffer - 1),
                    allow_edge_bias=True,
                )
                if relaxed_ranked and relaxed_ranked[0][1] > best_fallback_score:
                    best_fallback, best_fallback_score = relaxed_ranked[0]

            if spawn_tile is None:
                if best_fallback is not None:
                    spawn_tile = best_fallback
                else:
                    sampled_tiles = available_tiles[:]
                    sampled_tiles.sort(
                        key=lambda tile: score_tile(
                            tile,
                            profile=scoring_profile,
                            map_dimensions=self.base.world.get_size(),
                        )
                    )
                    if sampled_tiles:
                        spawn_tile = sampled_tiles[-1]

            if spawn_tile is None:
                raise Exception("No suitable spawn location found for a player")

            occupied_tiles.append(spawn_tile)
            available_tiles = [tile for tile in candidate_tiles() if tile is not spawn_tile]

            Settler.spawn_on(spawn_tile, player)
            units_created += 1

            companion_tile = self._find_best_companion_tile(spawn_tile, scoring_profile)
            if companion_tile is not None:
                ClubMan.spawn_on(companion_tile, player)
                units_created += 1

        return units_created > 0

    def _rank_start_tiles(
        self,
        candidates: List["Tile"],
        occupied_tiles: List["Tile"],
        scoring_profile: TileScoringProfile,
        min_distance: int,
        max_attempts: int,
        land_ratio_threshold: float,
        land_check_radius: int,
        map_edge_buffer: int,
        allow_edge_bias: bool = False,
    ) -> List[Tuple["Tile", float]]:
        ranked: List[Tuple[Tile, float]] = []

        for tile in candidates:
            if TileRepository.is_near_map_edge(self.base.world.get_size(), tile, map_edge_buffer) and not allow_edge_bias:
                continue

            if occupied_tiles and not all(TileRepository.hex_distance(tile, other) >= min_distance for other in occupied_tiles):
                continue

            neighbors = TileRepository.get_neighbors(tile, radius=land_check_radius)
            land_tiles = sum(1 for neighbor in neighbors if not neighbor.is_water)
            land_ratio = land_tiles / max(1, len(neighbors))
            if land_ratio < land_ratio_threshold:
                continue

            ranked.append(
                (
                    tile,
                    score_tile(
                        tile,
                        profile=scoring_profile,
                        map_dimensions=self.base.world.get_size(),
                        allow_edge_bias=allow_edge_bias,
                    ),
                )
            )

        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked[:max_attempts]

    def _find_best_companion_tile(self, spawn_tile: "Tile", scoring_profile: TileScoringProfile) -> Optional["Tile"]:
        adjacent_tiles = TileRepository.get_neighbors(spawn_tile, radius=1)
        candidate_tiles = [tile for tile in adjacent_tiles if tile.is_spawnable_upon() and tile.is_passable()]
        if not candidate_tiles:
            return None

        candidate_tiles.sort(
            key=lambda tile: score_tile(
                tile,
                profile=scoring_profile,
                map_dimensions=self.base.world.get_size(),
            ),
            reverse=True,
        )
        return candidate_tiles[0]

    def _get_scoring_profile(self) -> TileScoringProfile:
        return get_dynamic_tile_scoring_profile(
            str(self.setup_options.get("map_script", "continents")),
            str(self.setup_options.get("biome_style", "balanced")),
        )
