from logging import Logger
from random import randint, randrange
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type, cast
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
from helpers.colors import Colors
from managers.entity import EntityManager, EntityType
from managers.i18n import T_TranslationOrStrOrNone
from managers.log import LogManager
from system.effects import Effects
from system.entity import BaseEntity

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
        self.entity_key = self.tag
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
        self.border_growth_rate: float = 1.5
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
        self.building: BaseCityImprovement | Unit | None = None  # can be either improvement or unit

        self._improvements: ImprovementsSet = ImprovementsSet()
        self.effects: Effects = Effects(self)
        self.icons: Dict[str, str] = {}

        self.register()

    def dump(self) -> Dict[str, Any]:
        next_tile: str | None = (
            _next_tile.get_tag()
            if self.border_growth_next_tile is not None and ((_next_tile := self.border_growth_next_tile()) is not None)
            else None
        )

        if self.building is not None:
            _building: BaseCityImprovement | Unit | None = self.get_building()
            assert _building is not None, "Building reference is None, it has been destroyed."
            building: Dict[str, Any] | None = _building.dump()
        else:
            building = None

        return {
            "name": self.name,  # type: ignore
            "hidden_in_tree": self.hidden_in_tree,
            "tag": self.tag,
            "entity_key": self.entity_key,
            "entity_type_ref": self.entity_type_ref,
            "tile_tag": self.get_tile().get_tag(),
            "owner_tag": self.get_owner().get_tag() if self.get_owner() else None,
            "_improvements": self._improvements.dump(),
            "population": self.population,
            "is_capital": self.is_capital,
            "border_growth_points": self.border_growth_points,
            "border_growth_cost": self.border_growth_cost,
            "border_growth_next_tile": next_tile,
            "resource_required": {"cls_ref": f"{self.resource_required.__module__}.{self.resource_required.__name__}"}
            if self.resource_required
            else None,
            "resource_required_amount": self.resource_required_amount.dump() if self.resource_required_amount else None,
            "resource_collected": self.resource_collected.dump(),
            "food_collected": self.food_collected.dump(),
            "population_food_usage": self.population_food_usage,
            "new_population_food_required": self.new_population_food_required.dump(),
            "is_building": self.is_building,
            "building": building,
            "effects": self.effects.dump(),
            "owned_tiles": [tile.get_tag() for tile in self.owned_tiles],
            "icons": self.icons,
            "_health_left": self._health_left,
        }

    def add_icon(self, name: str, icon: str):
        self.icons[name] = icon

    def get_icon(self, name: str) -> Optional[str]:
        return self.icons.get(name)

    def delete_icon(self, name: str):
        if name in self.icons:
            del self.icons[name]

    def load_state(self) -> None:
        entity_manager: EntityManager = EntityManager.get_singleton_instance()

        self.tile = cast(ReferenceType["Tile"], entity_manager.get_ref_weak(EntityType.TILE, self.tile_tag))  # type:ignore
        self.owner = cast(ReferenceType["Player"], entity_manager.get_ref_weak(EntityType.PLAYER, self.owner_tag))

        self.logger = (
            self.get_owner().logger.getChild("city")
            if self.get_owner()
            else LogManager.get_singleton_instance().gameplay.getChild("city")
        )

        self.resource_required = (
            entity_manager.dynamic_import(self.resource_required["cls_ref"]) if self.resource_required else None  # type:ignore
        )

        self.resource_required_amount = (
            Yields.from_dict(self.resource_required_amount) if self.resource_required_amount else Yields.nullYield()  # type:ignore
        )
        self.resource_collected = (
            Yields.from_dict(self.resource_collected) if self.resource_collected else Yields.nullYield()  # type:ignore
        )
        self.new_population_food_required: Yields = Yields(
            food=population_curve(self.population, self.FOOD_EXPONENT, self.FOOD_BASE_REQUIREMENT)
        )
        self.food_collected = Yields.from_dict(self.food_collected)  # type:ignore

        _improvements = ImprovementsSet()
        _improvements.load_state(self._improvements)  # type:ignore
        self._improvements = _improvements

        _effects = Effects(self)
        _effects.load_state(self.effects)  # type:ignore
        self.effects = _effects

        self.get_owner().capital = ref(self) if self.is_capital else None

        if self.border_growth_next_tile is not None:
            self.border_growth_next_tile = cast(
                ReferenceType["Tile"],
                entity_manager.get_ref_weak(EntityType.TILE, self.border_growth_next_tile),  # type:ignore
            )  # type:ignore
        else:
            self.recalculate_border_growth_next_tile()

        self.owned_tiles = [  #  type:ignore
            cast("Tile", entity_manager.get_ref(EntityType.TILE, _tile_tag))  #  type:ignore
            for _tile_tag in self.owned_tiles  # type:ignore
        ]  # type:ignore

        if self.building is not None:
            _building_class: str = self.building.get("cls_ref", None)  # type:ignore
            if _building_class is not None:
                _building: Type[BaseCityImprovement | Unit] = EntityManager.dynamic_import(_building_class)  # type:ignore
                building: BaseCityImprovement | Unit = _building.__new__(_building)  # type:ignore
                building.__dict__.update(self.building)  # type:ignore
                building.load_state()  # type:ignore
                self.building = building  # type:ignore
                self.is_building = True
        else:
            self.building = None
            self.is_building = False

        self.population_food_usage = self.population_food_usage if self.population_food_usage else 1.0

        self.icons = self.icons if self.icons else {}

        self.is_registered = True
        self.register_handlers()

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

    def register_handlers(self):
        self.accept(f"game.gameplay.city.gets_tile_ownership_{self.tag}", self.on_tile_ownership_changed)
        self.accept(
            f"game.gameplay.city.request_start_building_improvement_{self.tag}",
            self.on_request_start_building_improvement,
        )
        self.accept(f"game.gameplay.city.request_start_building_unit_{self.tag}", self.on_request_start_building_unit)
        self.accept(f"game.gameplay.city.request_cancel_building_improvement_{self.tag}", self.on_cancel_building)

    def register(self):
        from managers.entity import EntityManager, EntityType

        if not self.is_registered:
            self.register_handlers()
            entity_manager: EntityManager = EntityManager.get_singleton_instance()
            entity_manager.register(entity=self, type=EntityType.CITY, key=self.tag)

    def build(self, improvement: "Improvement"):
        improvement.register()
        self._improvements.add(improvement)

    def get_next_border_growth_tile(self) -> Optional["Tile"]:
        if self.border_growth_next_tile is None:
            return None
        return self.border_growth_next_tile()

    def get_building(self) -> Optional["BaseCityImprovement | Unit"]:
        if self.building is None:
            return None
        return self.building

    def on_inspect(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        from gameplay.improvements.core.city.base_city_improvement import BaseCityImprovement
        from gameplay.unit import Unit

        building: BaseCityImprovement | Unit | None = self.building if self.building is not None else None
        assert building is None or isinstance(building, (BaseCityImprovement, Unit)), (
            "Building is not an instance of BaseCityImprovement or Unit."
        )

        next_tile = (
            None
            if (self.border_growth_next_tile is None or (next_tile := self.border_growth_next_tile()) is None)
            else next_tile.get_tag()
        )

        data = {
            "key": self.entity_key,
            "entity_key": self.entity_key,
            "entity_type_ref": EntityType.CITY.value,
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
            "icons": self.icons,
        }
        return data, self.get_children_inspect()

    def get_children_inspect(self) -> Dict[str, Any]:
        data = {
            "improvements": set(self._improvements.get_all()),
            "effects": set(self.effects.get_effects().values()),
        }
        return data

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

        self.get_tile().get_renderer().update()

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
            building: BaseCityImprovement | Unit | None = self.building
            building.owner = self.get_owner()
            building.tile = self.get_tile()

            assert building is not None, "Building reference is None, it has been destroyed."

            self.is_building = False
            self.resource_collected = self.resource_collected - self.resource_required_amount
            self.resource_required = None

            if isinstance(building, BaseCityImprovement):
                self.build(building)  # type: ignore
                MessengerGlobal.messenger.send("game.gameplay.city.finish_building_improvement", [self, building])

            elif isinstance(building, Unit):  # type: ignore
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
        self.new_population_food_required = Yields(
            food=population_curve(self.population, self.FOOD_EXPONENT, self.FOOD_BASE_REQUIREMENT)
        )
        food_surplus = Yields(food=self.calculate_food_surplus())

        if food_surplus.food.value < 0:
            if (self.food_collected + food_surplus) <= Yields.nullYield():
                self.starve_population()
                self.get_tile().render()
            else:
                self.food_collected -= food_surplus
        elif food_surplus.food.value > 0:
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
                self.player.capital = ref(self)

    def birth(self, population: int = 1, *args: Any, **kwargs: Any):
        for _ in range(population):
            self.citizens.create(*args, **kwargs)

    def on_citizen_birth(self, citizen: Any):  # Placeholder
        self.population += 1

    def de_capitalize(self):
        self.is_capital = False

    def assign_tile(self, tile: "Tile"):
        self.owned_tiles.append(tile)

    def remove_owned_tile(self, tile: "Tile"):
        self.owned_tiles.remove(tile)

    def recalculate_border_growth_cost(self) -> int:
        owned: int = len(self.owned_tiles)
        base_cost = 15
        self.border_growth_cost = max(base_cost, int(base_cost * (self.border_growth_rate**owned)))
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
                self.recalculate_border_growth_cost()
                return

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
        MessengerGlobal.messenger.send("ui.update.ui.refresh_city_ui", [self])
        MessengerGlobal.messenger.send("game.border.refresh")

    def starve_population(self):
        self.population -= 1
        self.new_population_food_required = Yields(food=population_curve(self.population))
        self.food_collected = self.new_population_food_required - Yields(food=1)
        MessengerGlobal.messenger.send("game.gameplay.city.population_starve", [self])
        MessengerGlobal.messenger.send("ui.update.ui.refresh_city_ui", [self])

    def get_improvements(self) -> ImprovementsSet:
        return self._improvements

    def get_population_icon(self) -> str:
        return f"assets/generated/icons/resources/core/basic/populationx128_{str(self.population)}.png"

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
        tile.city_owner = ref(instance)

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
            tile_yields -= improvement.get_maintenance_cost()

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
