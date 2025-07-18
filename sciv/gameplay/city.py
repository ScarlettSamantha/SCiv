from logging import Logger
from random import randint, randrange
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple, cast
from weakref import ReferenceType, ref

from direct.showbase import DirectObject, MessengerGlobal
from direct.showbase.MessengerGlobal import messenger
from gameplay.citizens import Citizens, population_curve
from gameplay.improvements.core.city.base_city_improvement import BaseCityImprovement
from gameplay.improvements.core.city.palace import Palace
from gameplay.improvements_set import ImprovementsSet
from gameplay.repositories.tile import TileRepository
from gameplay.resource import BaseResource
from gameplay.yields import Yields
from helpers.cache import Cache
from helpers.colors import Colors
from managers.entity import EntityManager, EntityType
from managers.i18n import T_TranslationOrStrOrNone
from managers.log import LogManager
from system.effects import Effects
from system.entity import BaseEntity

from sciv.gameplay.unit import Unit

if TYPE_CHECKING:
    from gameplay.improvement import Improvement
    from gameplay.player import Player
    from gameplay.tile import Tile
    from gameplay.unit import Unit


class City(BaseEntity, DirectObject.DirectObject):
    FOOD_EXPONENT: float = 1.5
    FOOD_BASE_REQUIREMENT: float = 10

    CITY_MAX_BORDER_GROWTH_RADIUS: int = 5

    def __init__(self, name: str, tile: "Tile", player: "Player | None", *args: Any, **kwargs: Any):
        super().__init__(tile=tile, owner=player, *args, **kwargs)

        self.name: T_TranslationOrStrOrNone = name
        self.owned_tiles: List[Tile] = []
        self.is_capital: bool = False
        self.logger: Logger = LogManager.get_singleton_instance().gameplay.getChild("city")
        self.tag = self.generate_tag()
        self.entity_type_ref = EntityType.CITY.value
        self._tile: ReferenceType[Tile] = ref(tile)

        self.active: bool = True
        self.destroyed: bool = False
        self.population: int = 1

        self.citizens: Citizens = Citizens()

        self.revolting: bool = False
        self.being_sieged: bool = False
        self.being_blockaded: bool = False

        self.border_growth_points: int = 0
        self.border_growth_cost: int = 10 * len(self.owned_tiles) + 10
        self.border_growth_next_tile: Optional[ReferenceType[Tile]] = None

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
        self.building: ReferenceType[BaseCityImprovement | Unit] | None = None  # can be either improvement or unit

        self._improvements: ImprovementsSet = ImprovementsSet()

        # @todo
        self.spies = []

        self.effects: Effects = Effects(self)

        self.register()

    def dumps(self) -> Dict[str, Any]:
        building: str | None = (
            None if (self.building is None or (is_building := self.building()) is None) else is_building.get_tag()
        )

        next_tile: str | None = (
            _next_tile.get_tag()
            if self.border_growth_next_tile is not None and ((_next_tile := self.border_growth_next_tile()) is not None)
            else None
        )

        return {
            "name": self.name,
            "tag": self.tag,
            "tile": self.get_tile().tag,
            "owner": self.get_owner().tag if self.get_owner() else None,
            "improvements": self._improvements.dump(),
            "population": self.population,
            "is_capital": self.is_capital,
            "border_growth_points": self.border_growth_points,
            "border_growth_cost": self.border_growth_cost,
            "border_growth_next_tile": next_tile,
            "is_building": self.is_building,
            "building": building,
            "effects": self.effects.dump(),
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        entity_manager: EntityManager = EntityManager.get_singleton_instance()

        self.name = state.get("name", "")
        self.tag = state.get("tag", "")
        tile_tag: str = state.get("tile", "")
        owner_tag: str = state.get("owner", "")
        self.population = state.get("population", 1)
        self.is_capital = state.get("is_capital", False)
        self.border_growth_points = state.get("border_growth_points", 0)
        self.border_growth_cost = state.get("border_growth_cost", 0)
        next_tile_tag: str | None = state.get("border_growth_next_tile")
        building_tag: str | None = state.get("building")

        if tile_tag:
            tile: ReferenceType["Tile"] | None = cast(
                ReferenceType["Tile"] | None, entity_manager.get_ref_weak(EntityType.TILE, tile_tag)
            )
            if tile is None:
                raise ValueError(f"Tile with tag {tile_tag} not found.")
            self._tile = tile

        if owner_tag:
            player: ReferenceType["Player"] | None = cast(
                ReferenceType["Player"] | None, entity_manager.get_ref_weak(EntityType.PLAYER, owner_tag)
            )
            if player is None:
                raise ValueError(f"Player with tag {owner_tag} not found.")
            self._owner = player

        if next_tile_tag:
            next_tile: ReferenceType["Tile"] | None = cast(
                ReferenceType["Tile"] | None, entity_manager.get_ref_weak(EntityType.TILE, next_tile_tag)
            )
            if next_tile is not None:
                self.border_growth_next_tile = next_tile

        if building_tag:
            building: ReferenceType[BaseCityImprovement | Unit] | None = cast(
                ReferenceType[BaseCityImprovement | Unit] | None,
                EntityManager.get_singleton_instance().get_ref(EntityType.IMPROVEMENT, building_tag),
            )
            if building is not None:
                self.building = building

        if "effects" in state:
            effects = Effects(self)
            effects.load_state(state["effects"])
            self.effects = effects

        if "improvements" in state:
            self._improvements = ImprovementsSet()
            self._improvements.load_state(state["improvements"])

    @property
    def player(self) -> "Player | None":
        if self._owner is None:
            self.logger.error("Player reference is no longer valid.")
            return None
        player: Player | None = self.get_owner()
        assert player is not None, "Player reference is no longer valid."
        return player

    @player.setter
    def player(self, value: "Player"):
        self._owner = ref(value)

    def generate_tag(self):
        return f"city_{self.get_tile().x}_{str(self.get_tile().y)}_{str(self.name).replace(' ', '_').lower()}_{str(randrange(2**5, 2**8))}"

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

    def get_next_border_growth_tile(self) -> Optional["Tile"]:
        if self.border_growth_next_tile is None:
            return None
        return self.border_growth_next_tile()

    def get_building(self) -> Optional["BaseCityImprovement | Unit"]:
        if self.building is None:
            return None
        return self.building()

    def on_inspect(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        is_building: ReferenceType[BaseCityImprovement | Unit] | None = (
            self.building if self.building is not None else None
        )

        building = None if is_building is None or (_building := is_building()) is None else _building.get_tag()
        next_tile = (
            None
            if (self.border_growth_next_tile is None or (next_tile := self.border_growth_next_tile()) is None)
            else next_tile.get_tag()
        )

        data = {
            "key": self.entity_key,
            "tag": self.tag,
            "name": self.name,
            "description": self.description,
            "tile": self.get_tile().tag,
            "owner": f"[color={Colors.to_hex(self.player.get_color())}]{str(self.player.get_name())}[/color]"
            if self.player is not None
            else None,
            "population": self.population,
            "population_food_usage": self.population_food_usage,
            "food_collected": self.food_collected.on_inspect(basic=True),
            "new_population_food_required": self.new_population_food_required.on_inspect(basic=True),
            "border_growth_points": self.border_growth_points,
            "border_growth_cost": self.border_growth_cost,
            "border_growth_next_tile": next_tile,
            "is_capital": self.is_capital,
            "is_building": self.is_building,
            "building": building,
            "resource_required": self.resource_required if self.resource_required is not None else None,
            "resource_required_amount": self.resource_required_amount.on_inspect(basic=True),
            "resource_collected": self.resource_collected.on_inspect(basic=True),
        }
        return data, self.get_children_inspect()

    def __getstate__(self) -> Dict[str, Any]:
        state = self.__dict__.copy()
        state.pop("logger", None)
        state.pop("base", None)
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        self.__dict__.update(state)
        self.logger = LogManager.get_singleton_instance().gameplay.getChild("city")
        self.base = Cache.get_showbase_instance()

    def get_children_inspect(self) -> Dict[str, Set[Any] | List[Any]]:
        return {
            "improvements": set(self._improvements.get_all()),
            "effects": set(self.effects.get_effects().values()),
        }

    def calculate_food_surplus(self) -> float:
        return self.calculate_yield_from_tiles().only(["food"]).food.value - (
            self.population_food_usage * self.population
        )

    def on_turn_end(self, turn: int) -> None:
        self.logger.debug(f"City {self.name} is processing turn {turn}.")

        self.effects.on_turn_end(turn)  # Execute before yields are calculated as effects can modify yields.

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
        production = tile_yield.only(["production"])
        self.resource_collected += production
        from gameplay.unit import Unit

        if self.resource_collected.only(["production"]) >= self.resource_required_amount and self.building is not None:
            self.logger.debug(f"City {self.name} has collected enough resources to build {self.building}.")
            building: BaseCityImprovement | Unit | None = self.building()

            assert building is not None, "Building reference is None, it has been destroyed."

            self.is_building = False
            self.resource_collected = self.resource_collected - self.resource_required_amount
            self.resource_required = None

            if isinstance(building, BaseCityImprovement):
                self._improvements.add(building)
                MessengerGlobal.messenger.send("game.gameplay.city.finish_building_improvement", [self, building])
            elif isinstance(building, Unit):  # type: ignore
                if self.player is not None:
                    self.player.units.add_unit(building)

                tile_to_spawn = None
                if not self.get_tile().get_units().has_any():
                    tile_to_spawn: ReferenceType[Tile] | Tile | None = self.tile
                else:
                    radius: List[int] = [1, 2, 3, 4]
                    for r in radius:
                        tiles: List[Tile] = TileRepository.get_neighbors(self.get_tile(), r)
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

                building.is_being_build = False
                building.spawn_on(self.tile(), self.player)  # type: ignore
                self.get_tile().render()

                MessengerGlobal.messenger.send("game.gameplay.city.finish_building_unit", [self, building])
            else:
                raise RuntimeError("Building is not an instance of BaseCityImprovement or Unit.")

            self.building = None
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
                self.get_tile().render()
            else:
                self.food_collected -= food_surplus
        elif food_surplus.food.value > 0:
            # If food storage plus surplus meets/exceeds the required food, grow population.
            food_stored: Yields = self.food_collected.only(["food"])
            if (food_stored + food_surplus) >= self.new_population_food_required:
                self.grow_population()
                self.get_tile().render()
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

    def assign_tile(self, tile: "Tile"):
        self.owned_tiles.append(tile)

    def remove_owned_tile(self, tile: "Tile"):
        self.owned_tiles.remove(tile)

    def recalculate_border_growth_cost(self) -> int:
        self.border_growth_cost = 10 * len(self.owned_tiles) + 10
        return self.border_growth_cost

    def recalculate_border_growth_next_tile(self):
        max_radius = self.CITY_MAX_BORDER_GROWTH_RADIUS
        center_tile = self.get_tile()

        for radius in range(1, max_radius + 1):
            neighbors: List["Tile"] = TileRepository.get_neighbors(center_tile, radius)
            available_tiles: List["Tile"] = [
                tile for tile in neighbors if tile.city is None and tile not in self.owned_tiles
            ]

            if available_tiles:
                resource_tiles: List["Tile"] = []
                for tile in available_tiles:
                    if tile.resources.flatten():
                        resource_tiles.append(tile)
                if resource_tiles:
                    self.border_growth_next_tile = ref(resource_tiles[randint(0, len(resource_tiles) - 1)])
                else:
                    self.border_growth_next_tile = ref(available_tiles[randint(0, len(available_tiles) - 1)])
                self.border_growth_cost = (5 * (len(self.owned_tiles) - 7)) + (5 * (radius - 1))
                return

        # If no tile is found in any radius
        self.border_growth_next_tile = None

    def on_border_growth(self):
        self.border_growth_points -= self.border_growth_cost
        self.recalculate_border_growth_cost()
        self.recalculate_border_growth_next_tile()
        MessengerGlobal.messenger.send("game.gameplay.city.border_growth", [self])

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
        self.building = ref(improvement)

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
        self.building = ref(unit)

        MessengerGlobal.messenger.send("game.gameplay.city.starts_building_unit", [self, unit])

    def on_turn_change_stage_city(self, city: "City", turn: int):
        if city != self:
            return

        self.on_turn_end(turn)

    def on_tile_ownership_changed(self, city: "City", tile: "Tile"):
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
        tile: "Tile",
        owner: "Player",
        population: int = 1,
        is_capital: bool = False,
        auto_claim_radius: int = 0,
    ) -> "City":
        instance = City(name=name, tile=tile, player=owner)
        instance.population = population
        instance.is_capital = is_capital
        owner.add_city(instance)
        tile.city = instance
        tile.city_owner = instance

        if auto_claim_radius > 0:
            from gameplay.repositories.tile import TileRepository

            adjacent_tiles: List[Tile] = TileRepository.get_neighbors(
                tile,
                auto_claim_radius,
                check_passable=False,
            )
            for adjacent_tile in adjacent_tiles:
                messenger.send("game.gameplay.city.requests_tile", [instance, adjacent_tile])

        if is_capital:
            instance.build(Palace(tile, owner))

        return instance

    def calculate_yield_from_tiles(self) -> Yields:
        tile_yields = Yields()

        for tile in self.owned_tiles:
            tile_yields += tile.get_tile_yield()

        for improvement in self._improvements.get_all():
            tile_yields += improvement.tile_yield_improvement
            tile_yields -= improvement.maintenance_cost

            for improvement_effect in improvement.effects.get_effects().values():
                tile_yields += improvement_effect.yield_impact
                tile_yields -= improvement_effect.maintenance_impact

        return tile_yields

    def get_yield(self) -> Yields:
        _yield = Yields.nullYield()

        for improvement in self._improvements.get_all():
            _yield += improvement.tile_yield_improvement

            for improvement_effect in improvement.effects.get_effects().values():
                _yield += improvement_effect.yield_impact

        return _yield

    def has_improvement(self, improvement: "BaseCityImprovement") -> bool:
        return self._improvements.has(improvement)
