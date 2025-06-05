from logging import Logger
from random import randint
from typing import TYPE_CHECKING, Any, List, Optional

from direct.showbase import DirectObject, MessengerGlobal
from direct.showbase.MessengerGlobal import messenger

from gameplay.citizens import Citizens, population_curve
from gameplay.improvements.core.city.base_city_improvement import BaseCityImprovement
from gameplay.improvements.core.city.palace import Palace
from gameplay.improvements_set import ImprovementsSet
from gameplay.resource import BaseResource
from gameplay.yields import Yields
from managers.i18n import T_TranslationOrStrOrNone
from managers.log import LogManager
from system.effects import Effects
from system.entity import BaseEntity
from gameplay.repositories.tile import TileRepository

if TYPE_CHECKING:
    from gameplay.improvement import Improvement
    from gameplay.player import Player
    from gameplay.tiles.base_tile import BaseTile
    from gameplay.unit import Unit


class City(BaseEntity, DirectObject.DirectObject):
    logger: Logger = LogManager.get_singleton_instance().gameplay.getChild("city")

    FOOD_EXPONENT: float = 1.5
    FOOD_BASE_REQUIREMENT: float = 10

    CITY_MAX_BORDER_GROWTH_RADIUS: int = 5

    def __init__(self, name: str, tile: "BaseTile", *args: Any, **kwargs: Any):
        super().__init__(tile=tile, *args, **kwargs)
        from gameplay.player import Player

        self.name: T_TranslationOrStrOrNone = name
        self.player: Optional[Player] = None
        self.owned_tiles: List[BaseTile] = []
        self.is_capital: bool = False

        self.active: bool = True
        self.destroyed: bool = False
        self.population: int = 1

        self.citizens: Citizens = Citizens()

        self.revolting: bool = False
        self.being_sieged: bool = False
        self.being_blockaded: bool = False

        self.border_growth_points: int = 0
        self.border_growth_cost: int = 10 * len(self.owned_tiles) + 10
        self.border_growth_next_tile: Optional[BaseTile] = None

        self.tax_level: float = 0.0
        self.population_food_usage: float = 1.0
        self.new_population_food_required: Yields = Yields(
            food=population_curve(self.population, self.FOOD_EXPONENT, self.FOOD_BASE_REQUIREMENT)
        )
        self.food_collected: Yields = Yields.nullYield()

        self.is_building: bool = False
        self.resource_required: Optional[type[BaseResource]] = None
        self.resource_required_amount: Yields = Yields.nullYield()  # no-op
        self.resource_collected: Yields = Yields.nullYield()  # no-op # This is the amount of resources collected so far
        self.building: BaseCityImprovement | Unit | None = None  # can be either improvement or unit

        self._improvements: ImprovementsSet = ImprovementsSet()
        self.tag = ""
        # @todo
        self.spies = []

        if self.player is not None:
            self._register_object()

        self.effects: Effects = Effects(self)

        self.generate_tag()
        self.register()

    def generate_tag(self):
        self.tag = f"city_{str(randint(1, 100000000))}"

    def register(self):
        from managers.entity import EntityManager, EntityType

        self.accept(f"game.gameplay.city.gets_tile_ownership_{self.tag}", self.on_tile_ownership_changed)
        self.accept(
            f"game.gameplay.city.request_start_building_improvement_{self.tag}",
            self.on_request_start_building_improvement,
        )
        self.accept(f"game.gameplay.city.request_start_building_unit_{self.tag}", self.on_request_start_building_unit)
        self.accept(f"game.gameplay.city.request_cancel_building_improvement_{self.tag}", self.on_cancel_building)

        entity_manager: EntityManager = EntityManager.get_singleton_instance()
        entity_manager.register(entity=self, type=EntityType.CITY, key=self.tag)

    def build(self, improvement: "Improvement"):
        self._improvements.add(improvement)

    def calculate_food_surplus(self) -> float:
        return self.calculate_yield_from_tiles().only(["food"]).food.value - (
            self.population_food_usage * self.population
        )

    def on_turn_end(self, turn: int) -> None:
        self.logger.debug(f"City {self.name} is processing turn {turn}.")

        self.effects.on_turn_end(turn)  # Execute before yields are calculated as effects can modify yields.

        # Calculate yield once per turn
        yields: Yields = self.calculate_yield_from_tiles()

        self._process_food()
        if self.is_building and self.building is not None:
            self._process_production(yields)
        self._process_owner_contributions(yields)
        self._process_border_growth()

    def _process_border_growth(self) -> None:
        self.border_growth_points += int(self.calculate_yield_from_tiles().only(["culture"]).culture.value)

        if self.border_growth_next_tile is None:  # if no tile is assigned, recalculate
            self.recalculate_border_growth_next_tile()

        if self.border_growth_points >= self.border_growth_cost:
            MessengerGlobal.messenger.send("game.gameplay.city.requests_tile", [self, self.border_growth_next_tile])
            self.on_border_growth()

    def _process_owner_contributions(self, yields: Yields):
        if self.player is not None:
            self.player.contribute(yields.only(["gold", "faith", "science", "culture"]))

    def _process_production(self, tile_yield: Yields) -> None:
        """Process production: add resources and check if improvement is complete."""
        production = tile_yield.only(["production"])
        self.resource_collected += production
        from gameplay.unit import Unit

        if self.resource_collected.only(["production"]) >= self.resource_required_amount and self.building is not None:
            self.logger.debug(f"City {self.name} has collected enough resources to build {self.building.name}.")
            # Save current building reference before resetting it.
            building = self.building

            # Reset production state.
            self.is_building = False
            self.building = None
            self.resource_collected = Yields.nullYield()
            self.resource_required = None

            if isinstance(building, BaseCityImprovement):
                self._improvements.add(building)
                MessengerGlobal.messenger.send("game.gameplay.city.finish_building_improvement", [self, building])
            elif isinstance(building, Unit):  # type: ignore
                if self.player is not None:
                    self.player.units.add_unit(building)

                tile_to_spawn = None
                if (
                    not self.get_tile().get_units().has_any()
                ):  # If there are no units on the tile, spawn the unit on the city tile.
                    tile_to_spawn = self.tile
                else:
                    radius: List[int] = [1, 2, 3, 4]
                    for r in radius:  # Check for a tile to spawn the unit on. We check in a radius of 1, 2, 3, 4 tiles.
                        tiles = TileRepository.get_neighbors(self.get_tile(), r)
                        for tile in tiles:
                            if (
                                not tile.units.has_any()
                                and tile.is_passable()
                                and tile.is_occupied() is False
                                and tile.is_water is False
                            ):
                                tile_to_spawn = tile
                                break
                        if tile_to_spawn is not None:
                            break

                if tile_to_spawn is None:
                    raise AssertionError("Could not find a tile to spawn the unit on.")

                unit: Unit = building
                unit.tile = tile_to_spawn
                unit.owner = self.player
                unit.spawn()

                MessengerGlobal.messenger.send("game.gameplay.city.finish_building_unit", [self, building])
            self.logger.debug(f"City {self.name} has finished building improvement.")

    def _process_food(self) -> None:
        """Process food consumption and production to manage population changes."""
        self.new_population_food_required = Yields(
            food=population_curve(self.population, self.FOOD_EXPONENT, self.FOOD_BASE_REQUIREMENT)
        )
        food_surplus = Yields(food=self.calculate_food_surplus())

        if food_surplus.food.value < 0:
            # When the total food (storage + surplus) is negative, population starves.
            if (self.food_collected + food_surplus) <= Yields.nullYield():
                self.starve_population()
            else:
                self.food_collected -= food_surplus
        elif food_surplus.food.value > 0:
            # If food storage plus surplus meets/exceeds the required food, grow population.
            food_stored: Yields = self.food_collected.only(["food"])
            if (food_stored + food_surplus) >= self.new_population_food_required:
                self.grow_population()
            else:
                self.food_collected += food_surplus

    def promote_to_capital(self):
        self.is_capital = True

    def _register_object(self):
        if self.player is not None:
            self.player.cities.add(self)
            if self.is_capital:
                self.player.capital = self

    def birth(self, population: int = 1, *args: Any, **kwargs: Any):
        for _ in range(population):
            self.citizens.create(*args, **kwargs)

    def _register_callbacks(self):
        self.citizens.register_callback("on_birth", self.on_citizen_birth)

    def on_citizen_birth(self, citizen: Any):  # Placeholder
        self.population += 1

    def de_capitalize(self):
        self.is_capital = False

    def assign_tile(self, tile: "BaseTile"):
        self.owned_tiles.append(tile)

    def remove_owned_tile(self, tile: "BaseTile"):
        self.owned_tiles.remove(tile)

    def recalculate_border_growth_cost(self) -> int:
        self.border_growth_cost = 10 * len(self.owned_tiles) + 10
        return self.border_growth_cost

    def recalculate_border_growth_next_tile(self):
        max_radius = self.CITY_MAX_BORDER_GROWTH_RADIUS
        center_tile = self.get_tile()

        for radius in range(1, max_radius + 1):
            neighbors: List["BaseTile"] = TileRepository.get_neighbors(center_tile, radius)
            available_tiles: List["BaseTile"] = [
                tile for tile in neighbors if tile.city is None and tile not in self.owned_tiles
            ]

            if available_tiles:
                resource_tiles: List["BaseTile"] = []
                for tile in available_tiles:
                    if tile.resources.flatten():
                        resource_tiles.append(tile)
                if resource_tiles:
                    self.border_growth_next_tile = resource_tiles[randint(0, len(resource_tiles) - 1)]
                else:
                    self.border_growth_next_tile = available_tiles[randint(0, len(available_tiles) - 1)]
                self.border_growth_cost = (5 * (len(self.owned_tiles) - 7)) + (5 * (radius - 1))
                return

        # If no tile is found in any radius
        self.border_growth_next_tile = None

    def on_border_growth(self):
        self.border_growth_points -= self.border_growth_cost
        self.recalculate_border_growth_cost()
        self.recalculate_border_growth_next_tile()
        MessengerGlobal.messenger.send("game.gameplay.city.border_growth", [self])

    def get_next_border_growth_tile(self) -> Optional["BaseTile"]:
        if self.border_growth_next_tile is None:
            return None
        return self.border_growth_next_tile

    def on_request_start_building_improvement(self, city: "City", improvement: "BaseCityImprovement"):
        if city != self:  # This does not concern us
            return
        from gameplay.unit import Unit

        self.logger.debug(f"City {city.name} got request to build improvement {improvement.name}.")

        if not isinstance(improvement, BaseCityImprovement) and not isinstance(improvement, Unit):  # type: ignore
            self.logger.error("Improvement is not an instance of BaseCityImprovement or UnitBaseClass.")
            return

        if improvement in self._improvements:
            self.logger.error(
                f"City {self.name} is trying to build improvement {improvement.name} but it already exists."
            )

        self.is_building = True
        self.resource_required = improvement.resource_needed
        self.resource_required_amount = improvement.amount_resource_needed
        self.resource_collected = Yields.nullYield()
        self.building = improvement

        self.logger.debug(f"City {self.name} is starting to build improvement {improvement.name}. sending message.")
        MessengerGlobal.messenger.send("game.gameplay.city.starts_building_improvement", [self, improvement])

    def on_request_start_building_unit(self, city: "City", unit: "Unit"):
        if city != self:
            return

        self.logger.debug(f"City {city.name} got request to build unit {unit.name}.")

        self.is_building = True
        self.resource_required = unit.resource_needed
        self.resource_required_amount = unit.amount_resource_needed
        self.resource_collected = Yields.nullYield()
        self.building = unit

        MessengerGlobal.messenger.send("game.gameplay.city.starts_building_unit", [self, unit])

    def on_turn_change_stage_city(self, city: "City", turn: int):
        if city != self:
            return

        self.on_turn_end(turn)

    def on_tile_ownership_changed(self, city: "City", tile: "BaseTile"):
        if tile in self.owned_tiles:
            return
        self.assign_tile(tile)

    def on_cancel_building(self, city: "City"):
        if city != self:
            return

        self.logger.debug(f"City {city.name} is being told to cancel building.")
        self.is_building = False
        self.building = None
        self.resource_required = None
        self.resource_required_amount = Yields.nullYield()
        self.resource_collected = Yields.nullYield()
        MessengerGlobal.messenger.send("game.gameplay.city.canceled_production", [self])

    def grow_population(self):
        self.population += 1
        self.new_population_food_required = Yields(food=population_curve(self.population))
        self.food_collected = Yields.nullYield()
        MessengerGlobal.messenger.send("game.gameplay.city.grows_population", [self])
        MessengerGlobal.messenger.send("ui.update.ui.refresh_city_ui")
        MessengerGlobal.messenger.send("game.border.refresh")

    def starve_population(self):
        self.population -= 1
        self.new_population_food_required = Yields(food=population_curve(self.population))
        self.food_collected = (
            self.new_population_food_required - Yields(food=1)
        )  # We take the requirement for the lower population and subtract 1 this is to prevent the city from starving again next turn.
        MessengerGlobal.messenger.send("game.gameplay.city.population_starve", [self])
        MessengerGlobal.messenger.send("ui.update.ui.refresh_city_ui")

    def get_improvements(self) -> ImprovementsSet:
        return self._improvements

    def get_population_icon(self) -> str:
        return f"core/basic/populationx128_{str(self.population)}.png"

    @classmethod
    def found_new(
        cls,
        name: str,
        tile: "BaseTile",
        owner: "Player",
        population: int = 1,
        is_capital: bool = False,
        auto_claim_radius: int = 0,
    ) -> "City":
        instance = City(name=name, tile=tile)
        instance.player = owner
        instance.population = population
        instance.is_capital = is_capital
        instance.player.add_city(instance)
        tile.city = instance
        tile.city_owner = instance

        if is_capital:
            instance.build(Palace())

        if auto_claim_radius > 0:
            from gameplay.repositories.tile import TileRepository

            adjacent_tiles: List[BaseTile] = TileRepository.get_neighbors(
                tile,
                auto_claim_radius,
                check_passable=False,
            )
            for adjacent_tile in adjacent_tiles:
                cls.logger.debug(
                    f"City {instance.name} is requesting claiming tile {adjacent_tile.tag}, sending message."
                )
                messenger.send("game.gameplay.city.requests_tile", [instance, adjacent_tile])

        return instance

    def calculate_yield_from_tiles(self) -> Yields:
        tile_yields = Yields()

        for tile in self.owned_tiles:
            tile_yields += tile.get_tile_yield()

        for improvement in self._improvements.get_all():
            tile_yields += improvement.tile_yield_improvement
            tile_yields -= improvement.maintenance_cost

        return tile_yields

    def get_yield(self) -> Yields:
        _yield = Yields.nullYield()
        for improvement in self._improvements.get_all():
            _yield += improvement.tile_yield_improvement

        return _yield
