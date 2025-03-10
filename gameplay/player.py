import weakref
from typing import TYPE_CHECKING, Literal, Optional, Self

from gameplay._units import Units
from gameplay.cities import Cities
from gameplay.citizen import Citizen
from gameplay.citizens import Citizens
from gameplay.city import City
from gameplay.civilization import Civilization
from gameplay.claims import Claims
from gameplay.effect import Effect, Effects
from gameplay.goverment import Goverment
from gameplay.leader import Leader
from gameplay.mood import Mood
from gameplay.moods import Moods
from gameplay.personality import Personality
from gameplay.player_tiles import PlayerTiles
from gameplay.relationships import Relationships
from gameplay.resource import Resources
from gameplay.trades import Trades
from gameplay.votes import Votes
from helpers.colors import Colors, Tuple4f
from system.entity import BaseEntity

if TYPE_CHECKING:
    from gameplay.units.unit_base import UnitBaseClass


class Player(BaseEntity):
    def __init__(
        self,
        name: str,
        turn_order: int,
        personality: Personality,
        civilization: Civilization,
        leader: Leader,
        color: Optional[Tuple4f] = None,
    ) -> None:
        super().__init__()
        from gameplay._units import Units

        self.name: str = name
        self.id: str | None = None
        self.identifier: str | None = None
        self.color: Tuple4f = color if color else Colors.sequence()

        self.turn_order: int = turn_order

        self.is_human: int = 0
        self.is_being_controlled: int = 0
        self.instanace_controlling: int = 0

        self.personality: Personality = personality
        self.civilization: Civilization = civilization
        self.leader: Leader = leader

        self.mood: Mood = Mood()
        self.moods: Moods = Moods()
        self.relationships: Relationships = Relationships()

        self.focus = None  # @todo
        self.commitment = 0  # @todo
        self.goal: None = None  # @todo

        self.war_readiness: int = 0  # can be negative and postive.
        self.war_exaustion: int = 0  # can be negative and postive.

        self.size_penalty: float = 0  # 0-3, multiplicative penalty based on the size of the empire.
        self.population_pentality: float = 0  # 0-3, multiplicative penalty based on the population of the empire.
        self.population: int = 0  # total population of the empire.
        self.citizens: Citizens = (
            Citizens()
        )  # keeps track of the citizens in the empire, but citizens are primarially stored in cities.

        # Empire stats
        self.revolt: float = 0.0  # revolt is a percentage of the empire that is in revolt. 0-100
        self.anarchy: float = 0.0  # anarchy is a percentage of the empire that is in anarchy. 0-100
        self.subpression: float = 0.0  # multiplicative bonus on the effectiveness of subpression operations and opression of revolt and anarchy.
        self.popularity: float = 0.0  # 0-100, percentage of the population that supports the goverment. This is not loyality to the goverment, but support for the empire in general. (not a border mechanic)
        self.taxes: int = 0  # 0-100, percentage of the civilian income that is taxed.

        self.police_effectiveness: float = 0.0  # 0-3 multiplier on the effectiveness of police operations.
        self.counter_intelligence_effectiveness: float = (
            0.0  # 0-3 multiplier on the effectiveness of counter intelligence operations.
        )

        self.world_standing: float = 0.0  # can be negative or positive, 0 is neutral. range is only implied and not defined. but can be assumed to be -100 to 100
        self.delegates: float = 0.0  # absolute number of delegates the player has in the world congress.

        self.goverment_strength = 0
        self.goverment: Goverment = Goverment()

        self.cities: Cities = Cities()
        self.capital: City | None = (
            None  # Capital city of the player, can be None if player has no cities and just a settler or an endgame condition has been met.
        )
        self.tiles: PlayerTiles = PlayerTiles()
        self.claims: Claims = Claims()
        self.units: Units = Units()
        self.votes: Votes = Votes()

        self.trades: Trades = Trades()

        self.resources: Resources = Resources()
        # self.greats: Greats = Greats()

        self.effects: Effects = Effects()

        self._register_callbacks()

    def register(self) -> None:
        from managers.entity import EntityManager, EntityType

        EntityManager.get_instance().register(entity=self, type=EntityType.PLAYER, key=f"{self.name}-{self.turn_order}")

    def unregister(self) -> None:
        from managers.entity import EntityManager, EntityType

        EntityManager.get_instance().unregister(entity=self, type=EntityType.PLAYER)

    def _register_callbacks(self) -> None:
        self.citizens.register_callback(event="on_birth", callback=self.on_citizen_birth)

    # @todo make citizens seperate thing.
    def on_citizen_birth(self, citizen: Citizen) -> None:
        self.population += 1

    def _recalculate(self) -> None:
        properties: tuple[
            Literal["citizens"],
            Literal["revolt"],
            Literal["anarchy"],
            Literal["subpression"],
            Literal["popularity"],
        ] = ("citizens", "revolt", "anarchy", "subpression", "popularity")
        city_loop_needed: bool = False
        for prop in properties:
            if prop == "citizens":
                city_loop_needed = True
            else:
                pass

        def _city_loop(self: Self) -> None:
            self.citizens.reset()
            for city in self.cities:
                self.citizens.create(num=city.population)

        if city_loop_needed:
            _city_loop(self=self)

    def getEffect(self, key: str) -> Effect | None:
        return self.effects.get(key=key)

    def getEffects(self) -> Effects:
        return self.effects

    def addEffect(self, key: str, effect: Effect) -> None:
        self.effects.add(effect=effect, key_or_auto=key)

    def addUnit(self, unit: "UnitBaseClass") -> None:
        self.units.add_unit(unit)

    def removeUnit(self, unit: "UnitBaseClass") -> None:
        self.units.remove_unit(unit)

    def destroy(self):
        """Player is destroyed or wiped out."""
        self.unregister()

    def get_units(self) -> Units:
        return self.units

    def get_all_units(self) -> list[weakref.ReferenceType["UnitBaseClass"]]:
        return self.get_units().all()
